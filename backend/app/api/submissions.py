"""Enhanced Submissions API endpoints with comprehensive logging."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
from functools import wraps
import uuid
import json
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.log_service import LogService as ApplicationInsightsLogger
from app.logging import get_logger, log_function, log_exceptions
from app.logging.core import request_id_var, user_id_var, campaign_id_var

# Initialize structured logger
logger = get_logger(__name__)

# Create FastAPI router (converted from Flask Blueprint)
# router = APIRouter(prefix="/api/submissions", tags=["submissions"], redirect_slashes=False)
router = APIRouter(tags=["submissions"], redirect_slashes=False)

# Simulated submission storage
SUBMISSIONS_DB = {}
SUBMISSION_STATS = {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "spam": 0}


# Pydantic models for request/response
class SubmissionCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=10000)
    type: str = Field(...)
    metadata: Optional[Dict[str, Any]] = Field(default={})


class StatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = ""


def log_submission_operation(func):
    """Decorator for logging submission operations."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        operation = func.__name__.replace("_", " ").title()
        start_time = time.time()

        # Extract request and user from function arguments
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
            "user_agent": (
                request.headers.get("User-Agent", "Unknown") if request else "Unknown"
            ),
        }

        # Add user context if available
        if current_user:
            context["user_id"] = str(current_user.id)
        else:
            context["user_id"] = "anonymous"

        # Extract submission ID from kwargs
        if "submission_id" in kwargs:
            context["submission_id"] = kwargs["submission_id"]

        logger.info(f"Starting submission operation: {operation}", context=context)

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"Submission operation completed: {operation}",
                context={
                    **context,
                    "duration": duration,
                    "status": "success",
                },
            )

            # Log performance for slow operations (Fixed: replaced log_performance)
            if duration > 1.0:
                logger.warning(
                    f"Slow operation detected: {operation}",
                    context={
                        **context,
                        "duration": duration,
                        "performance_threshold_exceeded": True,
                    },
                )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Submission operation failed: {operation}",
                context={
                    **context,
                    "duration": duration,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise

    return wrapper


def validate_submission_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate submission data."""
    required_fields = ["title", "content", "type"]

    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    # Validate content length
    if len(data.get("content", "")) > 10000:
        return False, "Content too long (max 10000 characters)"

    if len(data.get("title", "")) > 200:
        return False, "Title too long (max 200 characters)"

    # Validate submission type
    valid_types = ["form", "feedback", "report", "inquiry", "application"]
    if data.get("type") not in valid_types:
        return (
            False,
            f"Invalid submission type. Must be one of: {', '.join(valid_types)}",
        )

    return True, None


def check_spam(submission_data: Dict[str, Any]) -> bool:
    """Check if submission is spam."""
    # Simple spam detection (implement more sophisticated logic)
    spam_keywords = ["viagra", "casino", "lottery", "prize", "winner"]
    content = submission_data.get("content", "").lower()
    title = submission_data.get("title", "").lower()

    for keyword in spam_keywords:
        if keyword in content or keyword in title:
            logger.warning(
                "Potential spam detected",
                context={
                    "keyword": keyword,
                    "submission_type": submission_data.get("type"),
                },
            )
            return True

    return False


def is_admin(user: User) -> bool:
    """Check if user is an admin (implement your logic)."""
    # Placeholder - implement actual admin check
    # You might check user.role or similar
    return False


@router.post("/submit")
@log_submission_operation
def create_submission(
    request: Request,
    submission_data: SubmissionCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None),  # Allow anonymous submissions
):
    """Create a new submission."""
    try:
        data = submission_data.model_dump()
        app_logger = ApplicationInsightsLogger(db)

        # Get user context
        user_id = str(current_user.id) if current_user else "anonymous"

        if current_user:
            app_logger.set_context(user_id=str(current_user.id))

        # Validate submission data
        is_valid, error_message = validate_submission_data(data)
        if not is_valid:
            logger.warning(
                "Invalid submission data",
                context={
                    "error": error_message,
                    "user_id": user_id,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            raise HTTPException(status_code=400, detail=error_message)

        # Check for spam
        is_spam = check_spam(data)

        # Create submission
        submission_id = str(uuid.uuid4())
        submission = {
            "id": submission_id,
            "user_id": user_id,
            "title": data["title"],
            "content": data["content"],
            "type": data["type"],
            "metadata": data.get("metadata", {}),
            "status": "spam" if is_spam else "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        }

        # Store submission
        SUBMISSIONS_DB[submission_id] = submission

        # Update stats
        SUBMISSION_STATS["total"] += 1
        if is_spam:
            SUBMISSION_STATS["spam"] += 1

            # Fixed: replaced log_security_event with proper logging
            app_logger.track_security_event(
                event_name="spam_submission",
                user_id=user_id,
                ip_address=request.client.host if request.client else "unknown",
                success=False,
                details={
                    "submission_id": submission_id,
                    "submission_type": data["type"],
                },
            )
        else:
            SUBMISSION_STATS["pending"] += 1

        logger.info(
            "Submission created successfully",
            context={
                "submission_id": submission_id,
                "user_id": user_id,
                "type": data["type"],
                "status": submission["status"],
            },
        )

        return {
            "success": True,
            "submission_id": submission_id,
            "status": submission["status"],
            "message": "Submission created successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create submission",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "ip": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(status_code=500, detail="Failed to create submission")


@router.get("/{submission_id}")
@log_submission_operation
def get_submission(
    submission_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific submission."""
    try:
        user_id = str(current_user.id)
        app_logger = ApplicationInsightsLogger(db)
        app_logger.set_context(user_id=user_id)

        # Check if submission exists
        if submission_id not in SUBMISSIONS_DB:
            logger.warning(
                "Submission not found",
                context={"submission_id": submission_id, "user_id": user_id},
            )
            raise HTTPException(status_code=404, detail="Submission not found")

        submission = SUBMISSIONS_DB[submission_id]

        # Check access permissions
        if submission["user_id"] != user_id and not is_admin(current_user):
            logger.warning(
                "Unauthorized submission access attempt",
                context={
                    "submission_id": submission_id,
                    "user_id": user_id,
                    "owner_id": submission["user_id"],
                },
            )

            # Fixed: replaced log_security_event with proper logging
            app_logger.track_security_event(
                event_name="unauthorized_submission_access",
                user_id=user_id,
                ip_address=request.client.host if request.client else "unknown",
                success=False,
                details={
                    "submission_id": submission_id,
                    "owner_id": submission["user_id"],
                },
            )

            raise HTTPException(status_code=403, detail="Unauthorized access")

        logger.info(
            "Submission retrieved",
            context={"submission_id": submission_id, "user_id": user_id},
        )

        return {"success": True, "submission": submission}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve submission",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "submission_id": submission_id,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve submission")


@router.get("/list")
@log_submission_operation
def list_submissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    """List submissions with filtering and pagination."""
    try:
        user_id = str(current_user.id)
        app_logger = ApplicationInsightsLogger(db)
        app_logger.set_context(user_id=user_id)

        logger.info(
            "Listing submissions",
            context={
                "user_id": user_id,
                "page": page,
                "per_page": per_page,
                "filters": {"status": status, "type": type},
            },
        )

        # Filter submissions
        filtered_submissions = []
        for submission_id, submission in SUBMISSIONS_DB.items():
            # Check access
            if submission["user_id"] != user_id and not is_admin(current_user):
                continue

            # Apply filters
            if status and submission["status"] != status:
                continue
            if type and submission["type"] != type:
                continue

            filtered_submissions.append(submission)

        # Sort submissions
        reverse_order = sort_order == "desc"
        if sort_by == "created_at":
            filtered_submissions.sort(
                key=lambda x: x["created_at"], reverse=reverse_order
            )
        elif sort_by == "status":
            filtered_submissions.sort(key=lambda x: x["status"], reverse=reverse_order)

        # Paginate
        total = len(filtered_submissions)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered_submissions[start:end]

        logger.info(
            "Submissions listed successfully",
            context={
                "user_id": user_id,
                "total_results": total,
                "returned_results": len(paginated),
            },
        )

        return {
            "success": True,
            "submissions": paginated,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
            },
        }

    except Exception as e:
        logger.error(
            "Failed to list submissions",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to list submissions")


@router.put("/{submission_id}/status")
@log_submission_operation
def update_submission_status(
    submission_id: str,
    status_data: StatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update submission status (admin only)."""
    try:
        user_id = str(current_user.id)
        app_logger = ApplicationInsightsLogger(db)
        app_logger.set_context(user_id=user_id)

        new_status = status_data.status
        reason = status_data.reason

        # Validate status
        valid_statuses = ["pending", "reviewing", "approved", "rejected", "spam"]
        if new_status not in valid_statuses:
            logger.warning(
                "Invalid status update attempt",
                context={
                    "submission_id": submission_id,
                    "user_id": user_id,
                    "invalid_status": new_status,
                },
            )
            raise HTTPException(
                status_code=400,
                detail=f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
            )

        # Check if submission exists
        if submission_id not in SUBMISSIONS_DB:
            logger.warning(
                "Status update for non-existent submission",
                context={"submission_id": submission_id, "user_id": user_id},
            )
            raise HTTPException(status_code=404, detail="Submission not found")

        submission = SUBMISSIONS_DB[submission_id]
        old_status = submission["status"]

        # Update status
        submission["status"] = new_status
        submission["status_reason"] = reason
        submission["status_updated_by"] = user_id
        submission["status_updated_at"] = datetime.utcnow().isoformat()
        submission["updated_at"] = datetime.utcnow().isoformat()

        # Update stats
        if old_status in SUBMISSION_STATS:
            SUBMISSION_STATS[old_status] = max(0, SUBMISSION_STATS[old_status] - 1)
        if new_status in SUBMISSION_STATS:
            SUBMISSION_STATS[new_status] += 1

        logger.info(
            "Submission status updated",
            context={
                "submission_id": submission_id,
                "user_id": user_id,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
            },
        )

        # Log security event for important status changes (Fixed: replaced log_security_event)
        if new_status in ["approved", "rejected"]:
            app_logger.track_security_event(
                event_name=f"submission_{new_status}",
                user_id=user_id,
                ip_address=request.client.host if request.client else "unknown",
                success=True,
                details={
                    "submission_id": submission_id,
                    "reason": reason,
                    "old_status": old_status,
                },
            )

        return {
            "success": True,
            "message": "Status updated successfully",
            "old_status": old_status,
            "new_status": new_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update submission status",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "submission_id": submission_id,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to update status")


@router.delete("/{submission_id}")
@log_submission_operation
def delete_submission(
    submission_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a submission."""
    try:
        user_id = str(current_user.id)
        app_logger = ApplicationInsightsLogger(db)
        app_logger.set_context(user_id=user_id)

        # Check if submission exists
        if submission_id not in SUBMISSIONS_DB:
            logger.warning(
                "Delete attempt for non-existent submission",
                context={"submission_id": submission_id, "user_id": user_id},
            )
            raise HTTPException(status_code=404, detail="Submission not found")

        submission = SUBMISSIONS_DB[submission_id]

        # Check permissions
        if submission["user_id"] != user_id and not is_admin(current_user):
            logger.warning(
                "Unauthorized submission delete attempt",
                context={
                    "submission_id": submission_id,
                    "user_id": user_id,
                    "owner_id": submission["user_id"],
                },
            )

            # Fixed: replaced log_security_event with proper logging
            app_logger.track_security_event(
                event_name="unauthorized_submission_delete",
                user_id=user_id,
                ip_address=request.client.host if request.client else "unknown",
                success=False,
                details={
                    "submission_id": submission_id,
                    "owner_id": submission["user_id"],
                },
            )

            raise HTTPException(status_code=403, detail="Unauthorized")

        # Delete submission
        status_val = submission["status"]
        del SUBMISSIONS_DB[submission_id]

        # Update stats
        if status_val in SUBMISSION_STATS:
            SUBMISSION_STATS[status_val] = max(0, SUBMISSION_STATS[status_val] - 1)
        SUBMISSION_STATS["total"] = max(0, SUBMISSION_STATS["total"] - 1)

        logger.info(
            "Submission deleted",
            context={
                "submission_id": submission_id,
                "user_id": user_id,
                "submission_type": submission["type"],
            },
        )

        return {"success": True, "message": "Submission deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete submission",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "submission_id": submission_id,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to delete submission")


@router.get("/stats")
@log_submission_operation
def get_submission_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get submission statistics."""
    try:
        user_id = str(current_user.id)
        app_logger = ApplicationInsightsLogger(db)
        app_logger.set_context(user_id=user_id)

        # Calculate additional stats
        stats = SUBMISSION_STATS.copy()

        # Add time-based stats
        now = datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        this_week = now - timedelta(days=now.weekday())
        this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        stats["today"] = 0
        stats["this_week"] = 0
        stats["this_month"] = 0

        for submission in SUBMISSIONS_DB.values():
            created_at = datetime.fromisoformat(submission["created_at"])
            if created_at >= today:
                stats["today"] += 1
            if created_at >= this_week:
                stats["this_week"] += 1
            if created_at >= this_month:
                stats["this_month"] += 1

        logger.info(
            "Submission statistics retrieved",
            context={"user_id": user_id, "total_submissions": stats["total"]},
        )

        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            "Failed to get submission statistics",
            context={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
