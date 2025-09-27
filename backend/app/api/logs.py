"""Enhanced Logs API endpoints with comprehensive logging."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import json
import gzip
import csv
import re
from io import StringIO
from functools import wraps

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.log_service import LogService as ApplicationInsightsLogger
from app.logging import get_logger, log_function, log_exceptions
from app.logging.core import request_id_var, user_id_var, campaign_id_var

# Initialize structured logger
logger = get_logger(__name__)

# Create FastAPI router (converted from Flask Blueprint)
router = APIRouter(prefix="/api/logs", tags=["logs"], redirect_slashes=False)

# Simulated log storage (in production, use proper log management system)
LOG_BUFFER = []
MAX_LOG_BUFFER = 10000


def log_operation(func):
    """Decorator for logging operations on logs."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        operation = func.__name__.replace("_", " ").title()
        start_time = time.time()

        # Extract request from function arguments
        request = None
        current_user = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
        for key, value in kwargs.items():
            if key == "current_user" and isinstance(value, User):
                current_user = value

        context = {
            "operation": operation,
            "endpoint": request.url.path if request else "unknown",
            "method": request.method if request else "unknown",
            "ip": request.client.host if request and request.client else "unknown",
            "user_id": str(current_user.id) if current_user else None,
        }

        logger.info(f"Starting log operation: {operation}", context=context)

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"Log operation completed: {operation}",
                context={
                    **context,
                    "duration": duration,
                    "status": "success",
                },
            )

            # Log performance for slow operations
            if duration > 2.0:
                logger.warning(
                    f"Slow operation detected: {operation}",
                    context={
                        **context,
                        "duration": duration,
                    },
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Log operation failed: {operation}",
                context={
                    **context,
                    "duration": duration,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    return wrapper


def validate_log_access(user_id: str, log_level: str = None) -> bool:
    """Validate if user has access to view logs."""
    # Implement your access control logic here
    # For now, returning True for demonstration
    if log_level in ["ERROR", "CRITICAL", "SECURITY"]:
        logger.info(
            "Validating sensitive log access",
            context={"user_id": user_id, "log_level": log_level},
        )
    return True


def parse_log_query(query_params: dict) -> Dict[str, Any]:
    """Parse and validate log query parameters."""
    parsed = {
        "level": query_params.get("level", "INFO").upper(),
        "start_time": None,
        "end_time": None,
        "source": query_params.get("source"),
        "user_id": query_params.get("user_id"),
        "limit": min(int(query_params.get("limit", 100)), 1000),
        "offset": int(query_params.get("offset", 0)),
        "search": query_params.get("search"),
        "format": query_params.get("format", "json"),
    }

    # Parse time parameters
    if query_params.get("start_time"):
        try:
            parsed["start_time"] = datetime.fromisoformat(query_params["start_time"])
        except ValueError:
            logger.warning(
                "Invalid start_time format",
                context={"start_time": query_params["start_time"]},
            )

    if query_params.get("end_time"):
        try:
            parsed["end_time"] = datetime.fromisoformat(query_params["end_time"])
        except ValueError:
            logger.warning(
                "Invalid end_time format",
                context={"end_time": query_params["end_time"]},
            )

    return parsed


@router.get("/query")
@log_operation
def query_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    level: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    format: str = Query("json"),
):
    """Query and retrieve logs based on filters."""
    try:
        user_id_val = str(current_user.id)
        query_params = parse_log_query(
            {
                "level": level,
                "start_time": start_time,
                "end_time": end_time,
                "source": source,
                "user_id": user_id,
                "limit": limit,
                "offset": offset,
                "search": search,
                "format": format,
            }
        )

        # Check access
        if not validate_log_access(user_id_val, query_params["level"]):
            logger.warning(
                "Unauthorized log access attempt",
                context={
                    "user_id": user_id_val,
                    "requested_level": query_params["level"],
                },
            )

            # Log security event
            app_logger = ApplicationInsightsLogger(db)
            app_logger.track_security_event(
                event_name="unauthorized_log_access",
                user_id=user_id_val,
                ip_address=request.client.host if request.client else "unknown",
                success=False,
                details={"requested_level": query_params["level"]},
            )

            raise HTTPException(status_code=403, detail="Unauthorized access to logs")

        logger.info(
            "Processing log query",
            context={"user_id": user_id_val, "query_params": query_params},
        )

        # Simulate log retrieval (replace with actual log system query)
        logs = []

        # Filter logs based on criteria
        filtered_logs = LOG_BUFFER.copy()

        if query_params["level"]:
            filtered_logs = [
                log
                for log in filtered_logs
                if log.get("level") == query_params["level"]
            ]

        if query_params["start_time"]:
            filtered_logs = [
                log
                for log in filtered_logs
                if datetime.fromisoformat(log["timestamp"])
                >= query_params["start_time"]
            ]

        if query_params["end_time"]:
            filtered_logs = [
                log
                for log in filtered_logs
                if datetime.fromisoformat(log["timestamp"]) <= query_params["end_time"]
            ]

        if query_params["search"]:
            pattern = re.compile(query_params["search"], re.IGNORECASE)
            filtered_logs = [
                log for log in filtered_logs if pattern.search(log.get("message", ""))
            ]

        # Apply pagination
        total_count = len(filtered_logs)
        start_idx = query_params["offset"]
        end_idx = start_idx + query_params["limit"]
        paginated_logs = filtered_logs[start_idx:end_idx]

        logger.info(
            "Log query completed",
            context={
                "user_id": user_id_val,
                "total_results": total_count,
                "returned_results": len(paginated_logs),
            },
        )

        return {
            "success": True,
            "logs": paginated_logs,
            "total": total_count,
            "offset": query_params["offset"],
            "limit": query_params["limit"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to query logs",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")


@router.get("/stream")
@log_operation
def stream_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    level: str = Query("INFO"),
):
    """Stream real-time logs."""
    try:
        user_id_val = str(current_user.id)
        level = level.upper()

        if not validate_log_access(user_id_val, level):
            logger.warning(
                "Unauthorized log streaming attempt",
                context={"user_id": user_id_val, "requested_level": level},
            )
            raise HTTPException(status_code=403, detail="Unauthorized")

        logger.info(
            "Starting log stream", context={"user_id": user_id_val, "level": level}
        )

        def generate():
            """Generate log stream."""
            last_index = 0

            while True:
                # Get new logs
                if last_index < len(LOG_BUFFER):
                    new_logs = LOG_BUFFER[last_index:]
                    last_index = len(LOG_BUFFER)

                    for log in new_logs:
                        if log.get("level") == level or level == "ALL":
                            yield f"data: {json.dumps(log)}\n\n"

                time.sleep(1)  # Poll interval

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to stream logs",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to stream logs")


@router.post("/export")
@log_operation
def export_logs(
    request: Request,
    export_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export logs in various formats."""
    try:
        user_id_val = str(current_user.id)

        export_format = export_data.get("format", "json")
        compress = export_data.get("compress", False)
        filters = export_data.get("filters", {})

        logger.info(
            "Processing log export request",
            context={
                "user_id": user_id_val,
                "format": export_format,
                "compress": compress,
            },
        )

        # Query logs with filters
        query_params = parse_log_query(filters)

        # Get filtered logs (simplified for demo)
        exported_logs = LOG_BUFFER[: query_params["limit"]]

        # Format logs based on export type
        if export_format == "json":
            output = json.dumps(exported_logs, indent=2)
            content_type = "application/json"
        elif export_format == "csv":
            output = convert_logs_to_csv(exported_logs)
            content_type = "text/csv"
        elif export_format == "text":
            output = convert_logs_to_text(exported_logs)
            content_type = "text/plain"
        else:
            logger.warning(
                "Invalid export format requested",
                context={"user_id": user_id_val, "format": export_format},
            )
            raise HTTPException(status_code=400, detail="Invalid export format")

        # Compress if requested
        if compress:
            output = gzip.compress(output.encode())
            content_type = "application/gzip"

        logger.info(
            "Log export completed",
            context={
                "user_id": user_id_val,
                "format": export_format,
                "size_bytes": len(output),
                "log_count": len(exported_logs),
            },
        )

        # Return file
        filename = f'logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.{export_format}{".gz" if compress else ""}'

        return Response(
            content=output,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to export logs",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to export logs")


@router.get("/stats")
@log_operation
def get_log_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    range: str = Query("24h"),
):
    """Get log statistics and analytics."""
    try:
        user_id_val = str(current_user.id)
        time_range = range

        logger.info(
            "Generating log statistics",
            context={"user_id": user_id_val, "time_range": time_range},
        )

        # Calculate time window
        if time_range == "1h":
            start_time = datetime.utcnow() - timedelta(hours=1)
        elif time_range == "24h":
            start_time = datetime.utcnow() - timedelta(days=1)
        elif time_range == "7d":
            start_time = datetime.utcnow() - timedelta(days=7)
        elif time_range == "30d":
            start_time = datetime.utcnow() - timedelta(days=30)
        else:
            start_time = datetime.utcnow() - timedelta(days=1)

        # Generate statistics (simplified for demo)
        stats = {
            "total_logs": len(LOG_BUFFER),
            "time_range": time_range,
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "by_level": {
                "DEBUG": 0,
                "INFO": 0,
                "WARNING": 0,
                "ERROR": 0,
                "CRITICAL": 0,
            },
            "by_source": {},
            "error_rate": 0,
            "top_errors": [],
            "activity_timeline": [],
        }

        # Count logs by level
        for log in LOG_BUFFER:
            level = log.get("level", "INFO")
            if level in stats["by_level"]:
                stats["by_level"][level] += 1

            source = log.get("source", "unknown")
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        # Calculate error rate
        total_logs = len(LOG_BUFFER)
        error_logs = stats["by_level"]["ERROR"] + stats["by_level"]["CRITICAL"]
        if total_logs > 0:
            stats["error_rate"] = (error_logs / total_logs) * 100

        logger.info(
            "Log statistics generated",
            context={
                "user_id": user_id_val,
                "total_logs": stats["total_logs"],
                "error_rate": stats["error_rate"],
            },
        )

        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(
            "Failed to generate log statistics",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to generate statistics")


@router.delete("/purge")
@log_operation
def purge_logs(
    request: Request,
    purge_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Purge old logs (admin only)."""
    try:
        user_id_val = str(current_user.id)

        # Check admin permission (implement your own logic)
        # if not is_admin(user_id_val):
        #     raise HTTPException(status_code=403, detail='Unauthorized')

        older_than_days = purge_data.get("older_than_days", 30)
        level = purge_data.get("level")
        dry_run = purge_data.get("dry_run", True)

        logger.warning(
            "Log purge requested",
            context={
                "user_id": user_id_val,
                "older_than_days": older_than_days,
                "level": level,
                "dry_run": dry_run,
            },
        )

        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)

        # Count logs to be purged
        logs_to_purge = 0
        for log in LOG_BUFFER:
            log_time = datetime.fromisoformat(
                log.get("timestamp", datetime.utcnow().isoformat())
            )
            if log_time < cutoff_time:
                if not level or log.get("level") == level:
                    logs_to_purge += 1

        if not dry_run:
            # Perform actual purge
            original_count = len(LOG_BUFFER)
            LOG_BUFFER[:] = [
                log
                for log in LOG_BUFFER
                if datetime.fromisoformat(
                    log.get("timestamp", datetime.utcnow().isoformat())
                )
                >= cutoff_time
                or (level and log.get("level") != level)
            ]
            actual_purged = original_count - len(LOG_BUFFER)

            logger.warning(
                "Logs purged successfully",
                context={"user_id": user_id_val, "logs_purged": actual_purged},
            )

            # Log security event
            app_logger = ApplicationInsightsLogger(db)
            app_logger.track_security_event(
                event_name="logs_purged",
                user_id=user_id_val,
                ip_address=request.client.host if request.client else "unknown",
                success=True,
                details={
                    "logs_purged": actual_purged,
                    "older_than_days": older_than_days,
                },
            )

        return {
            "success": True,
            "dry_run": dry_run,
            "logs_to_purge": logs_to_purge,
            "cutoff_time": cutoff_time.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to purge logs",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to purge logs")


def convert_logs_to_csv(logs: List[Dict]) -> str:
    """Convert logs to CSV format."""
    output = StringIO()

    if logs:
        writer = csv.DictWriter(output, fieldnames=logs[0].keys())
        writer.writeheader()
        writer.writerows(logs)

    return output.getvalue()


def convert_logs_to_text(logs: List[Dict]) -> str:
    """Convert logs to plain text format."""
    lines = []
    for log in logs:
        line = f"[{log.get('timestamp', 'N/A')}] {log.get('level', 'INFO')}: {log.get('message', '')}"
        lines.append(line)

    return "\n".join(lines)


# Add sample log entry to buffer for demo
def add_log_entry(level: str, message: str, **kwargs):
    """Add a log entry to the buffer."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        **kwargs,
    }

    LOG_BUFFER.append(entry)

    # Maintain buffer size
    if len(LOG_BUFFER) > MAX_LOG_BUFFER:
        LOG_BUFFER.pop(0)
