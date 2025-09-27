# app/utils/logs.py
"""
Database logging utilities - updated to work with new logging system
Maintains backwards compatibility while integrating with enhanced logging
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session


def _conn(session_or_conn: Session | Connection) -> Connection:
    """
    Accept either a Session or Connection and return a Connection.
    """
    if hasattr(session_or_conn, "execute") and not hasattr(session_or_conn, "bind"):
        # Already a Connection
        return session_or_conn  # type: ignore[return-value]
    # Session: open a connection
    return session_or_conn.connection()  # type: ignore[return-value]


def _maybe_commit(db: Session | Connection, autocommit: bool) -> None:
    """
    Commit only if:
      - autocommit=True and
      - we're dealing with a Session (not a bare Connection)
    """
    if autocommit and isinstance(db, Session):
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise


# ------------------------------
# Generic app log -> public.logs
# ------------------------------
def insert_app_log(
    db: Session | Connection,
    *,
    message: str,
    level: str = "INFO",
    user_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    website_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,  # ISO8601 if you want to override default
    autocommit: bool = True,
) -> str:
    """
    Inserts into public.logs.
    Your live DB requires id + non-null timestamp, so we provide both.
    
    Enhanced with error handling and validation for new logging system.
    """
    conn = _conn(db)
    new_id = str(uuid.uuid4())
    
    # Validate and sanitize inputs
    if not message:
        message = "Empty log message"
    
    if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = "INFO"
    
    # Ensure context is serializable
    try:
        context_json = json.dumps(context or {})
    except (TypeError, ValueError) as e:
        context_json = json.dumps({"serialization_error": str(e), "original_type": str(type(context))})
    
    payload = {
        "id": new_id,
        "level": level,
        "message": str(message)[:1000],  # Truncate long messages
        "user_id": user_id,
        "campaign_id": campaign_id,
        "website_id": website_id,
        "organization_id": organization_id,
        "context": context_json,
        "timestamp": timestamp,  # may be None; SQL uses COALESCE to now()
    }
    
    try:
        conn.execute(
            text(
                """
                INSERT INTO public.logs
                    (id, level, message, user_id, campaign_id, website_id, organization_id, context, timestamp)
                VALUES
                    (:id, :level, :message, :user_id, :campaign_id, :website_id, :organization_id,
                     CAST(:context AS jsonb),
                     COALESCE(:timestamp, now()))
                """
            ),
            payload,
        )
        _maybe_commit(db, autocommit)
        return new_id
    except Exception as e:
        # Log error but don't fail completely
        print(f"Failed to insert app log: {e}")
        if autocommit and isinstance(db, Session):
            db.rollback()
        raise


# -----------------------------------
# Submission log -> public.submission_logs
# -----------------------------------
def insert_submission_log(
    db: Session | Connection,
    *,
    campaign_id: str,
    target_url: str,
    status: Optional[str] = None,
    details: Optional[str] = None,
    user_id: Optional[str] = None,
    website_id: Optional[str] = None,
    submission_id: Optional[str] = None,
    action: Optional[str] = None,
    timestamp: Optional[str] = None,  # ISO8601 if you want to override default
    autocommit: bool = True,
) -> str:
    """
    Inserts into public.submission_logs.
    Enhanced with validation and error handling.
    """
    conn = _conn(db)
    new_id = str(uuid.uuid4())
    
    # Validate required fields
    if not campaign_id:
        raise ValueError("campaign_id is required for submission logs")
    if not target_url:
        raise ValueError("target_url is required for submission logs")
    
    payload = {
        "id": new_id,
        "campaign_id": campaign_id,
        "target_url": str(target_url)[:500],  # Truncate long URLs
        "status": status,
        "details": str(details)[:1000] if details else None,  # Truncate long details
        "user_id": user_id,
        "website_id": website_id,
        "submission_id": submission_id,
        "action": action,
        "timestamp": timestamp,
    }
    
    try:
        conn.execute(
            text(
                """
                INSERT INTO public.submission_logs
                    (id, campaign_id, target_url, status, details, user_id, website_id, submission_id, action, timestamp)
                VALUES
                    (:id, :campaign_id, :target_url, :status, :details, :user_id, :website_id, :submission_id, :action,
                     COALESCE(:timestamp, now()))
                """
            ),
            payload,
        )
        _maybe_commit(db, autocommit)
        return new_id
    except Exception as e:
        print(f"Failed to insert submission log: {e}")
        if autocommit and isinstance(db, Session):
            db.rollback()
        raise


# -------------------------------
# System log -> public.system_logs
# -------------------------------
def insert_system_log(
    db: Session | Connection,
    *,
    action: Optional[str] = None,
    details: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    timestamp: Optional[str] = None,  # ISO8601 if you want to override default
    autocommit: bool = True,
) -> str:
    """
    Inserts into public.system_logs.
    Enhanced with validation and error handling.
    """
    conn = _conn(db)
    new_id = str(uuid.uuid4())
    
    payload = {
        "id": new_id,
        "user_id": user_id,
        "action": str(action)[:200] if action else None,  # Truncate long actions
        "details": str(details)[:1000] if details else None,  # Truncate long details
        "ip_address": str(ip_address)[:45] if ip_address else None,  # IPv6 max length
        "user_agent": str(user_agent)[:500] if user_agent else None,  # Truncate long user agents
        "timestamp": timestamp,
    }
    
    try:
        conn.execute(
            text(
                """
                INSERT INTO public.system_logs
                    (id, user_id, action, details, ip_address, user_agent, timestamp)
                VALUES
                    (:id, :user_id, :action, :details, :ip_address, :user_agent, COALESCE(:timestamp, now()))
                """
            ),
            payload,
        )
        _maybe_commit(db, autocommit)
        return new_id
    except Exception as e:
        print(f"Failed to insert system log: {e}")
        if autocommit and isinstance(db, Session):
            db.rollback()
        raise


# ------------------------------
# Captcha log -> public.captcha_logs
# ------------------------------
def insert_captcha_log(
    db: Session | Connection,
    *,
    submission_id: Optional[str],
    captcha_type: Optional[str] = None,
    solved: Optional[bool] = None,
    solve_time: Optional[float] = None,
    dbc_balance: Optional[float] = None,
    error: Optional[str] = None,
    timestamp: Optional[str] = None,  # ISO8601 if you want to override default
    autocommit: bool = True,
) -> str:
    """
    Inserts into public.captcha_logs.
    Enhanced with validation and error handling.
    """
    conn = _conn(db)
    new_id = str(uuid.uuid4())
    
    # Validate solve_time (should be reasonable)
    if solve_time is not None and (solve_time < 0 or solve_time > 300):  # 5 minutes max
        solve_time = None
    
    # Validate dbc_balance (should be reasonable)
    if dbc_balance is not None and dbc_balance < 0:
        dbc_balance = None
    
    payload = {
        "id": new_id,
        "submission_id": submission_id,
        "captcha_type": str(captcha_type)[:50] if captcha_type else None,
        "solved": solved,
        "solve_time": solve_time,
        "dbc_balance": dbc_balance,
        "error": str(error)[:500] if error else None,  # Truncate long errors
        "timestamp": timestamp,
    }
    
    try:
        conn.execute(
            text(
                """
                INSERT INTO public.captcha_logs
                    (id, submission_id, captcha_type, solved, solve_time, dbc_balance, error, timestamp)
                VALUES
                    (:id, :submission_id, :captcha_type, :solved, :solve_time, :dbc_balance, :error, COALESCE(:timestamp, now()))
                """
            ),
            payload,
        )
        _maybe_commit(db, autocommit)
        return new_id
    except Exception as e:
        print(f"Failed to insert captcha log: {e}")
        if autocommit and isinstance(db, Session):
            db.rollback()
        raise


# Helper functions for working with new logging system
def log_to_database_and_buffer(
    db: Session,
    level: str,
    message: str,
    user_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Helper function that logs to both database and new logging system
    Use this for critical logs that need both persistence and real-time access
    """
    # Log to database using existing function
    log_id = insert_app_log(
        db,
        message=message,
        level=level,
        user_id=user_id,
        campaign_id=campaign_id,
        context=context,
        autocommit=True
    )
    
    # Also log to new logging system for real-time access
    try:
        from app.logging import get_logger
        logger = get_logger("database_logger")
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message, context=context or {})
    except ImportError:
        # New logging system not available, continue with database only
        pass
    
    return log_id


# Batch operations for performance
def insert_app_logs_batch(
    db: Session | Connection,
    logs: list[Dict[str, Any]],
    autocommit: bool = True
) -> list[str]:
    """
    Insert multiple app logs in a single transaction for better performance
    """
    if not logs:
        return []
    
    conn = _conn(db)
    ids = []
    
    try:
        for log_data in logs:
            new_id = str(uuid.uuid4())
            ids.append(new_id)
            
            # Validate and prepare payload
            payload = {
                "id": new_id,
                "level": log_data.get("level", "INFO"),
                "message": str(log_data.get("message", ""))[:1000],
                "user_id": log_data.get("user_id"),
                "campaign_id": log_data.get("campaign_id"),
                "website_id": log_data.get("website_id"),
                "organization_id": log_data.get("organization_id"),
                "context": json.dumps(log_data.get("context", {})),
                "timestamp": log_data.get("timestamp"),
            }
            
            conn.execute(
                text(
                    """
                    INSERT INTO public.logs
                        (id, level, message, user_id, campaign_id, website_id, organization_id, context, timestamp)
                    VALUES
                        (:id, :level, :message, :user_id, :campaign_id, :website_id, :organization_id,
                         CAST(:context AS jsonb),
                         COALESCE(:timestamp, now()))
                    """
                ),
                payload,
            )
        
        _maybe_commit(db, autocommit)
        return ids
    except Exception as e:
        print(f"Failed to insert batch logs: {e}")
        if autocommit and isinstance(db, Session):
            db.rollback()
        raise