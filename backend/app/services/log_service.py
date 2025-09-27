# app/services/log_service.py
from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Deque, Dict, Optional

_pylogger = logging.getLogger(__name__)

_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "SYSTEM"}


def _coerce_level(value: Optional[str], default: str = "INFO") -> str:
    if not value:
        return default
    s = str(value).upper()
    return s if s in _LEVELS else default


@dataclass
class LogEvent:
    ts: str
    level: str
    message: str
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class LogService:
    _buffer: Deque[LogEvent] = deque(maxlen=2000)
    _lock = RLock()
    _streams: Dict[str, asyncio.Queue[LogEvent]] = {}

    def __init__(self, db_session: Any = None):
        self.db = db_session
        self._context_user_id = None
        self._context_campaign_id = None
        self._context_organization_id = None

    # ---------- class helpers ----------

    @classmethod
    def _now(cls) -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _append_event(
        cls,
        level: str,
        message: str,
        *,
        user_id: str | None = None,
        campaign_id: str | None = None,
        context: Dict[str, Any] | None = None,
    ) -> LogEvent:
        evt = LogEvent(
            ts=cls._now(),
            level=_coerce_level(level),
            message=str(message) if message is not None else "",
            user_id=user_id,
            campaign_id=campaign_id,
            context=context or {},
        )
        with cls._lock:
            cls._buffer.append(evt)
            if campaign_id and campaign_id in cls._streams:
                try:
                    cls._streams[campaign_id].put_nowait(evt)
                except Exception:
                    pass
        return evt

    @classmethod
    def _log_to_console(
        cls,
        level: str,
        message: str,
        *,
        user_id: str | None = None,
        campaign_id: str | None = None,
        context: Dict[str, Any] | None = None,
    ):
        log_level = getattr(logging, _coerce_level(level), logging.INFO)
        extra = context or {}
        if user_id:
            extra["user_id"] = user_id
        if campaign_id:
            extra["campaign_id"] = campaign_id
        try:
            _pylogger.log(
                log_level, str(message) if message is not None else "", extra=extra
            )
        except Exception:
            pass

    # ---------- CLASS API (message can be positional OR keyword) ----------

    @classmethod
    def append(
        cls,
        level_or_message: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        user_id = kwargs.pop("user_id", None)
        campaign_id = kwargs.pop("campaign_id", None)
        context = kwargs.pop("context", None)
        # ignore db/db_session at class level
        kwargs.pop("db_session", None)
        kwargs.pop("db", None)

        if kwargs and not context:
            context = kwargs
        elif kwargs and context:
            context.update(kwargs)

        level_kw = (
            context.pop("level", None) if context and "level" in context else None
        )
        level = _coerce_level(level_kw) if level_kw else None

        l_or_m = level_or_message
        msg = message

        if l_or_m and _coerce_level(l_or_m) in _LEVELS and msg is not None:
            level = _coerce_level(l_or_m)
            text = msg
        elif l_or_m and _coerce_level(l_or_m) in _LEVELS and msg is None:
            level = _coerce_level(l_or_m)
            text = ""
        elif l_or_m and (_coerce_level(l_or_m) not in _LEVELS):
            text = str(l_or_m)
            level = _coerce_level(level or "INFO")
        else:
            text = "" if msg is None else str(msg)
            level = _coerce_level(level or "INFO")

        cls._log_to_console(
            level, text, user_id=user_id, campaign_id=campaign_id, context=context
        )
        evt = cls._append_event(
            level, text, user_id=user_id, campaign_id=campaign_id, context=context
        )
        return asdict(evt)

    @classmethod
    def info(
        cls, message_or_first_arg: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        message = (
            message_or_first_arg
            if message_or_first_arg is not None
            else kwargs.pop("message", "")
        )
        # IMPORTANT: delegate to append (no recursion)
        return cls.append("INFO", message, **kwargs)

    @classmethod
    def warning(
        cls, message_or_first_arg: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        message = (
            message_or_first_arg
            if message_or_first_arg is not None
            else kwargs.pop("message", "")
        )
        return cls.append("WARNING", message, **kwargs)

    @classmethod
    def error(
        cls, message_or_first_arg: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        message = (
            message_or_first_arg
            if message_or_first_arg is not None
            else kwargs.pop("message", "")
        )
        return cls.append("ERROR", message, **kwargs)

    @classmethod
    def debug(
        cls, message_or_first_arg: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        message = (
            message_or_first_arg
            if message_or_first_arg is not None
            else kwargs.pop("message", "")
        )
        return cls.append("DEBUG", message, **kwargs)

    @classmethod
    def system_event(
        cls, message_or_first_arg: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        message = (
            message_or_first_arg
            if message_or_first_arg is not None
            else kwargs.pop("message", "")
        )
        return cls.append("SYSTEM", message, **kwargs)

    @classmethod
    def get_recent(cls, limit: int = 200) -> list[Dict[str, Any]]:
        with cls._lock:
            return [asdict(evt) for evt in list(cls._buffer)[-limit:]]

    @classmethod
    def snapshot(cls, campaign_id: str, *, limit: int = 500) -> list[str]:
        with cls._lock:
            items = (e for e in cls._buffer if e.campaign_id == campaign_id)
            out = [json.dumps(asdict(e), default=str) for e in items]
        if limit and len(out) > limit:
            out = out[-limit:]
        return out

    @classmethod
    async def stream(cls, campaign_id: str):
        q: asyncio.Queue[LogEvent] = asyncio.Queue()
        with cls._lock:
            cls._streams[campaign_id] = q
        try:
            for line in cls.snapshot(campaign_id, limit=50):
                yield f"data: {line}\n\n"
            while True:
                evt = await q.get()
                if evt.campaign_id == campaign_id:
                    yield f"data: {json.dumps(asdict(evt), default=str)}\n\n"
        finally:
            with cls._lock:
                cls._streams.pop(campaign_id, None)

    # ---------- INSTANCE API ----------

    def set_context(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None:
                if key == "user_id":
                    self._context_user_id = str(value)
                elif key == "campaign_id":
                    self._context_campaign_id = str(value)
                elif key == "organization_id":
                    self._context_organization_id = str(value)

    def track_business_event(
        self,
        event_name: str,
        properties: Dict[str, Any] = None,
        metrics: Dict[str, Any] = None,
    ):
        context = {
            "event": event_name,
            "properties": properties or {},
            "metrics": metrics or {},
        }
        return LogService.info(
            f"Business Event: {event_name}",
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )

    def track_workflow_step(
        self,
        workflow_name: str,
        step_name: str,
        step_number: int,
        total_steps: int,
        success: bool = True,
        properties: Dict[str, Any] = None,
    ):
        context = {
            "workflow": workflow_name,
            "step": step_name,
            "step_number": step_number,
            "total_steps": total_steps,
            "success": success,
            "properties": properties or {},
        }
        message = (
            f"Workflow: {workflow_name} - Step {step_number}/{total_steps}: {step_name}"
        )
        level = "INFO" if success else "WARNING"
        return LogService.append(
            level,
            message,
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )

    def track_database_operation(
        self,
        operation: str,
        table: str,
        query_time_ms: float = 0,
        success: bool = True,
        affected_rows: int = 0,
        query: str = None,
    ):
        context = {
            "operation": operation,
            "table": table,
            "query_time_ms": query_time_ms,
            "affected_rows": affected_rows,
            "success": success,
            "query": query,
        }
        return LogService.debug(
            f"DB {operation} on {table}: {query_time_ms}ms",
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )

    def track_authentication(
        self,
        action: str,
        email: str,
        success: bool,
        failure_reason: str = None,
        ip_address: str = None,
    ):
        context = {
            "action": action,
            "email": email,
            "success": success,
            "failure_reason": failure_reason,
            "ip_address": ip_address,
        }
        level = "INFO" if success else "WARNING"
        message = f"Auth {action} for {email}: {'Success' if success else failure_reason or 'Failed'}"
        return LogService.append(
            level,
            message,
            user_id=self._context_user_id,
            context=context,
            db_session=self.db,
        )

    def track_metric(self, name: str, value: float, properties: Dict[str, Any] = None):
        context = {
            "metric_name": name,
            "metric_value": value,
            "properties": properties or {},
        }
        return LogService.debug(
            f"Metric {name}: {value}",
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )

    def track_exception(
        self,
        exception: Exception,
        handled: bool = True,
        properties: Dict[str, Any] = None,
    ):
        context = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "handled": handled,
            "properties": properties or {},
        }
        level = "WARNING" if handled else "ERROR"
        message = f"{'Handled' if handled else 'Unhandled'} exception: {exception}"
        return LogService.append(
            level,
            message,
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )

    def track_user_action(
        self, action: str, target: str, properties: Dict[str, Any] = None
    ):
        context = {"action": action, "target": target, "properties": properties or {}}
        return LogService.info(
            f"User Action: {action} on {target}",
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )

    def track_dependency(
        self,
        name: str,
        dependency_type: str,
        target: str,
        duration_ms: float = 0,
        success: bool = True,
        result_code: str = None,
    ):
        context = {
            "dependency_name": name,
            "dependency_type": dependency_type,
            "target": target,
            "duration_ms": duration_ms,
            "success": success,
            "result_code": result_code,
        }
        level = "INFO" if success else "WARNING"
        message = f"Dependency: {name} ({dependency_type}) - {target}"
        return LogService.append(
            level,
            message,
            user_id=self._context_user_id,
            campaign_id=self._context_campaign_id,
            context=context,
            db_session=self.db,
        )


# Compatibility aliases
ApplicationInsightsLogger = LogService
SimpleApplicationLogger = LogService
EnhancedLogService = LogService


def log_method_execution(method_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                _pylogger.info(f"Executing method: {method_name}")
                result = func(*args, **kwargs)
                _pylogger.info(f"Method {method_name} completed successfully")
                return result
            except Exception as e:
                _pylogger.error(f"Method {method_name} failed: {e}")
                raise

        return wrapper

    return decorator


def app_info(*args, **kwargs):
    if args:
        return LogService.info(args[0], **kwargs)
    return LogService.info(**kwargs)


def app_warning(*args, **kwargs):
    if args:
        return LogService.warning(args[0], **kwargs)
    return LogService.warning(**kwargs)


def app_error(*args, **kwargs):
    if args:
        return LogService.error(args[0], **kwargs)
    return LogService.error(**kwargs)
