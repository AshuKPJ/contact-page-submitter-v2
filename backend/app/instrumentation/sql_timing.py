# app/instrumentation/sql_timing.py
from __future__ import annotations
import os
import time
from typing import Optional, Callable
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

DISABLED = os.getenv("SQL_TIMING_DISABLED", "false").lower() == "true"
SLOW_QUERY_MS = int(os.getenv("SQL_TIMING_SLOW_MS", "1000"))


def attach_listeners(
    engine: Engine, get_session: Optional[Callable[[], Session]] = None
) -> None:
    if DISABLED:
        return  # no-op

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        context._query_start_time = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start = getattr(context, "_query_start_time", None)
        if start is None:
            return
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if elapsed_ms < SLOW_QUERY_MS:
            return

        db: Optional[Session] = None
        try:
            if get_session:
                db = get_session()
            if db:
                from app.services.log_service import LogService

                LogService(db).warn(
                    message="slow_query_detected",
                    context={
                        "elapsed_ms": elapsed_ms,
                        "statement": (
                            (statement[:1997] + "...")
                            if len(statement) > 2000
                            else statement
                        ),
                        "parameters": (
                            (str(parameters)[:1997] + "...")
                            if len(str(parameters)) > 2000
                            else str(parameters)
                        ),
                    },
                )
        except Exception:
            pass
        finally:
            try:
                if db:
                    db.close()
            except Exception:
                pass
