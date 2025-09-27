# app/api/admin.py - Enhanced with comprehensive logging - FIXED VERSION
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

# Enhanced logging imports
from app.logging import get_logger, log_function, log_exceptions, log_performance
from app.logging.core import user_id_var, request_id_var

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize logger
logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"], redirect_slashes=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Safe schema imports with fallbacks
try:
    from app.schemas.admin import SystemStatus, UserManagement, AdminResponse
except ImportError:
    from pydantic import BaseModel
    from typing import Optional, Dict, Any, List, Literal, Union

    class SystemStatus(BaseModel):
        status: str
        database: str
        services: Dict[str, str]
        timestamp: str

    class UserManagement(BaseModel):
        user_id: str
        action: str
        reason: Optional[str] = None

    class AdminResponse(BaseModel):
        success: bool
        message: str
        data: Optional[Dict[str, Any]] = None


# User management models
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: str = "user"
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request and request.client:
        return request.client.host
    return "unknown"


@log_exceptions("check_admin_access")
def check_admin_access(current_user: User) -> bool:
    """Check if user has admin access - flexible check"""
    logger.debug(
        "Checking admin access",
        context={"user_id": str(current_user.id), "email": current_user.email},
    )

    try:
        role = getattr(current_user, "role", "user")
        if hasattr(role, "value"):
            role_str = str(role.value).lower()
        else:
            role_str = str(role).lower()

        # Allow admin, owner, or superuser roles
        has_access = role_str in ["admin", "owner", "superuser"]

        logger.auth_event(
            action="admin_access_check",
            email=current_user.email,
            success=has_access,
            user_role=role_str,
        )

        return has_access
    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={"user_id": str(current_user.id), "check_type": "admin_access"},
        )
        return False


def require_admin_access(current_user: User):
    """Require admin access or raise 403"""
    if not check_admin_access(current_user):
        logger.warning(
            "Admin access denied",
            context={
                "user_id": str(current_user.id),
                "email": current_user.email,
                "attempted_action": "require_admin_access",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Your current role does not have sufficient privileges.",
        )


@router.get("/system-status")
@log_function("get_system_status")
async def get_system_status(
    # Dependencies first
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # Request object last
    request: Request = None,
):
    """Get system status - admin only"""
    user_id_var.set(str(current_user.id))
    require_admin_access(current_user)

    client_ip = get_client_ip(request) if request else "unknown"

    logger.info(
        "System status check requested",
        context={
            "user_id": str(current_user.id),
            "admin_email": current_user.email,
            "ip": client_ip,
        },
    )

    try:
        # Test database connection
        db_start = time.time()
        db.execute(text("SELECT 1"))
        db_time = (time.time() - db_start) * 1000

        logger.database_operation(
            operation="HEALTH_CHECK", table="system", duration_ms=db_time, success=True
        )

        # Get basic system info
        try:
            # Check table existence
            tables_query = text(
                """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name IN ('users', 'campaigns', 'submissions', 'websites')
            """
            )
            tables_count = db.execute(tables_query).scalar() or 0

            status_data = {
                "status": "operational" if tables_count >= 4 else "degraded",
                "database": "connected",
                "response_time_ms": round(db_time, 2),
                "tables_available": int(tables_count),
                "services": {
                    "auth": "running",
                    "campaigns": "running",
                    "submissions": "running",
                    "analytics": "running",
                    "admin": "running",
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception:
            status_data = {
                "status": "degraded",
                "database": "connected",
                "response_time_ms": round(db_time, 2),
                "services": {
                    "auth": "unknown",
                    "campaigns": "unknown",
                    "submissions": "unknown",
                    "analytics": "unknown",
                    "admin": "running",
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        logger.info(
            f"System status: {status_data['status']}",
            context={
                "admin_id": str(current_user.id),
                "system_status": status_data["status"],
                "db_response_time": db_time,
                "tables_count": status_data.get("tables_available", 0),
            },
        )

        return status_data

    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={
                "endpoint": "/admin/system-status",
                "admin_id": str(current_user.id),
            },
        )
        return {
            "status": "error",
            "database": "error",
            "services": {
                "auth": "unknown",
                "campaigns": "unknown",
                "submissions": "unknown",
                "analytics": "unknown",
                "admin": "running",
            },
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/users")
@log_function("get_all_users")
async def get_all_users(
    # Query parameters first
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    # Dependencies next
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # Request object last
    request: Request = None,
):
    """Get all users with pagination - admin only"""
    user_id_var.set(str(current_user.id))
    require_admin_access(current_user)

    logger.info(
        "Admin users list request",
        context={
            "admin_id": str(current_user.id),
            "page": page,
            "per_page": per_page,
            "active_only": active_only,
            "ip": get_client_ip(request) if request else "unknown",
        },
    )

    try:
        query_start = time.time()

        # Build query
        base_query = """
            SELECT 
                id, email, first_name, last_name, role, 
                is_active, is_verified, created_at, updated_at,
                subscription_status, plan_id
            FROM users
        """
        count_query = "SELECT COUNT(*) FROM users"
        params = {}

        if active_only:
            base_query += " WHERE is_active = true"
            count_query += " WHERE is_active = true"

        # Get total count
        total = db.execute(text(count_query), params).scalar() or 0

        # Get paginated users
        offset = (page - 1) * per_page
        paginated_query = (
            f"{base_query} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )
        params.update({"limit": per_page, "offset": offset})

        users_result = db.execute(text(paginated_query), params).mappings().all()

        # Format users
        users = []
        for user_row in users_result:
            user_id = str(user_row["id"])

            try:
                stats_query = text(
                    """
                    SELECT 
                        (SELECT COUNT(*) FROM campaigns WHERE user_id = :user_id) as campaign_count,
                        (SELECT COUNT(*) FROM submissions WHERE user_id = :user_id) as submission_count,
                        (SELECT MAX(created_at) FROM campaigns WHERE user_id = :user_id) as last_campaign
                """
                )
                stats = (
                    db.execute(stats_query, {"user_id": user_id}).mappings().first()
                    or {}
                )
            except Exception:
                stats = {
                    "campaign_count": 0,
                    "submission_count": 0,
                    "last_campaign": None,
                }

            user_dict = {
                "id": user_id,
                "email": user_row["email"],
                "first_name": user_row.get("first_name"),
                "last_name": user_row.get("last_name"),
                "role": user_row.get("role", "user"),
                "is_active": user_row.get("is_active", True),
                "is_verified": user_row.get("is_verified", False),
                "subscription_status": user_row.get("subscription_status"),
                "created_at": (
                    user_row["created_at"].isoformat()
                    if user_row.get("created_at")
                    else None
                ),
                "updated_at": (
                    user_row["updated_at"].isoformat()
                    if user_row.get("updated_at")
                    else None
                ),
                "stats": {
                    "campaigns": int(stats.get("campaign_count", 0) or 0),
                    "submissions": int(stats.get("submission_count", 0) or 0),
                    "last_activity": (
                        stats["last_campaign"].isoformat()
                        if stats.get("last_campaign")
                        else None
                    ),
                },
            }
            users.append(user_dict)

        query_time = (time.time() - query_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="users",
            duration_ms=query_time,
            affected_rows=len(users),
            success=True,
            query_type="admin_users_list",
        )

        logger.info(
            f"Admin users list retrieved: {len(users)} users",
            context={
                "admin_id": str(current_user.id),
                "total_users": total,
                "page": page,
                "active_only": active_only,
                "query_time_ms": query_time,
            },
        )

        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    except Exception as e:
        logger.exception(
            e,
            handled=False,
            context={"endpoint": "/admin/users", "admin_id": str(current_user.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}",
        )


@router.post("/users")
@log_function("create_user")
async def create_user(
    # Request body first
    user_data: UserCreate,
    # Dependencies next
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # Request object last
    request: Request = None,
):
    """Create a new user - admin only"""
    user_id_var.set(str(current_user.id))
    require_admin_access(current_user)

    logger.info(
        "Admin user creation request",
        context={
            "admin_id": str(current_user.id),
            "new_user_email": user_data.email,
            "new_user_role": user_data.role,
            "ip": get_client_ip(request) if request else "unknown",
        },
    )

    try:
        # Check if user already exists
        existing_user = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_data.email},
        ).first()

        if existing_user:
            logger.warning(
                "User creation failed - email exists",
                context={
                    "admin_id": str(current_user.id),
                    "attempted_email": user_data.email,
                },
            )
            raise HTTPException(
                status_code=400, detail="User with this email already exists"
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user
        create_start = time.time()
        create_query = text(
            """
            INSERT INTO users (first_name, last_name, email, role, hashed_password, is_active, is_verified)
            VALUES (:first_name, :last_name, :email, :role, :hashed_password, true, true)
            RETURNING id, created_at
        """
        )

        result = db.execute(
            create_query,
            {
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "email": user_data.email,
                "role": user_data.role,
                "hashed_password": hashed_password,
            },
        ).first()

        db.commit()
        create_time = (time.time() - create_start) * 1000

        logger.database_operation(
            operation="INSERT",
            table="users",
            duration_ms=create_time,
            affected_rows=1,
            success=True,
        )

        logger.info(
            f"User created by admin: {user_data.email}",
            context={
                "admin_id": str(current_user.id),
                "new_user_id": str(result.id),
                "email": user_data.email,
                "role": user_data.role,
                "creation_time_ms": create_time,
            },
        )

        return {
            "id": str(result.id),
            "message": "User created successfully",
            "email": user_data.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(
            e,
            handled=False,
            context={
                "endpoint": "/admin/users",
                "admin_id": str(current_user.id),
                "attempted_email": user_data.email,
            },
        )
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.put("/users/{user_id}")
@log_function("update_user")
async def update_user(
    # Path parameters first
    user_id: str,
    # Request body next
    user_data: UserUpdate,
    # Dependencies next
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # Request object last
    request: Request = None,
):
    """Update a user - admin only"""
    user_id_var.set(str(current_user.id))
    require_admin_access(current_user)

    # Track what fields are being updated
    updated_fields = [
        k for k, v in user_data.model_dump(exclude_unset=True).items() if v is not None
    ]

    logger.info(
        "Admin user update request",
        context={
            "admin_id": str(current_user.id),
            "target_user_id": user_id,
            "fields_to_update": updated_fields,
            "ip": get_client_ip(request) if request else "unknown",
        },
    )

    try:
        # Check if user exists
        existing_user = db.execute(
            text("SELECT id, email FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).first()

        if not existing_user:
            logger.warning(
                "User update failed - user not found",
                context={"admin_id": str(current_user.id), "target_user_id": user_id},
            )
            raise HTTPException(status_code=404, detail="User not found")

        # Build update query dynamically
        update_start = time.time()
        update_fields = []
        params = {"user_id": user_id}

        if user_data.first_name is not None:
            update_fields.append("first_name = :first_name")
            params["first_name"] = user_data.first_name

        if user_data.last_name is not None:
            update_fields.append("last_name = :last_name")
            params["last_name"] = user_data.last_name

        if user_data.email is not None:
            update_fields.append("email = :email")
            params["email"] = user_data.email

        if user_data.role is not None:
            update_fields.append("role = :role")
            params["role"] = user_data.role

        if user_data.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = user_data.is_active

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_query = text(
            f"""
            UPDATE users 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :user_id
        """
        )

        db.execute(update_query, params)
        db.commit()

        update_time = (time.time() - update_start) * 1000

        logger.database_operation(
            operation="UPDATE",
            table="users",
            duration_ms=update_time,
            affected_rows=1,
            success=True,
        )

        logger.info(
            f"User updated by admin",
            context={
                "admin_id": str(current_user.id),
                "updated_user_id": user_id,
                "updated_user_email": existing_user.email,
                "fields_updated": updated_fields,
                "update_time_ms": update_time,
            },
        )

        return {"message": "User updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(
            e,
            handled=False,
            context={
                "endpoint": f"/admin/users/{user_id}",
                "admin_id": str(current_user.id),
                "fields_updating": updated_fields,
            },
        )
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.delete("/users/{user_id}")
@log_function("delete_user")
async def delete_user(
    # Path parameters first
    user_id: str,
    # Dependencies next
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # Request object last
    request: Request = None,
):
    """Delete a user - admin only"""
    user_id_var.set(str(current_user.id))
    require_admin_access(current_user)

    # Prevent self-deletion
    if str(current_user.id) == user_id:
        logger.warning(
            "Admin attempted self-deletion",
            context={"admin_id": str(current_user.id), "attempted_target": user_id},
        )
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    logger.info(
        "Admin user deletion request",
        context={
            "admin_id": str(current_user.id),
            "target_user_id": user_id,
            "ip": get_client_ip(request) if request else "unknown",
        },
    )

    try:
        # Check if user exists
        existing_user = db.execute(
            text("SELECT id, email FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).first()

        if not existing_user:
            logger.warning(
                "User deletion failed - user not found",
                context={"admin_id": str(current_user.id), "target_user_id": user_id},
            )
            raise HTTPException(status_code=404, detail="User not found")

        # Delete user (this will cascade to related records if configured)
        delete_start = time.time()
        delete_query = text("DELETE FROM users WHERE id = :user_id")
        db.execute(delete_query, {"user_id": user_id})
        db.commit()

        delete_time = (time.time() - delete_start) * 1000

        logger.database_operation(
            operation="DELETE",
            table="users",
            duration_ms=delete_time,
            affected_rows=1,
            success=True,
        )

        logger.info(
            f"User deleted by admin",
            context={
                "admin_id": str(current_user.id),
                "deleted_user_id": user_id,
                "deleted_email": existing_user.email,
                "deletion_time_ms": delete_time,
            },
        )

        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(
            e,
            handled=False,
            context={
                "endpoint": f"/admin/users/{user_id}",
                "admin_id": str(current_user.id),
            },
        )
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")


@router.get("/metrics")
@log_function("get_system_metrics")
async def get_system_metrics(
    # Dependencies first
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    # Request object last
    request: Request = None,
):
    """Get detailed system metrics - admin only"""
    user_id_var.set(str(current_user.id))
    require_admin_access(current_user)

    logger.info(
        "System metrics request",
        context={
            "admin_id": str(current_user.id),
            "ip": get_client_ip(request) if request else "unknown",
        },
    )

    try:
        metrics_start = time.time()

        # Get comprehensive metrics in one query to improve performance
        metrics_query = text(
            """
            SELECT 
                -- User metrics
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
                (SELECT COUNT(*) FROM users WHERE is_verified = true) as verified_users,
                (SELECT COUNT(*) FROM users WHERE role IN ('admin', 'owner')) as admin_users,
                
                -- Campaign metrics
                (SELECT COUNT(*) FROM campaigns) as total_campaigns,
                (SELECT COUNT(*) FROM campaigns WHERE status IN ('ACTIVE', 'running', 'PROCESSING')) as active_campaigns,
                (SELECT COUNT(*) FROM campaigns WHERE status IN ('COMPLETED', 'completed')) as completed_campaigns,
                (SELECT COUNT(*) FROM campaigns WHERE status IN ('FAILED', 'failed')) as failed_campaigns,
                
                -- Submission metrics
                (SELECT COUNT(*) FROM submissions) as total_submissions,
                (SELECT COUNT(*) FROM submissions WHERE success = true) as successful_submissions,
                (SELECT COUNT(*) FROM submissions WHERE success = false) as failed_submissions,
                (SELECT COUNT(*) FROM submissions WHERE status = 'pending') as pending_submissions,
                (SELECT COUNT(*) FROM submissions WHERE captcha_encountered = true) as captcha_submissions,
                
                -- Website metrics
                (SELECT COUNT(*) FROM websites) as total_websites,
                (SELECT COUNT(*) FROM websites WHERE form_detected = true) as websites_with_forms,
                (SELECT COUNT(*) FROM websites WHERE has_captcha = true) as websites_with_captcha,
                
                -- Recent activity
                (SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days') as new_users_week,
                (SELECT COUNT(*) FROM campaigns WHERE created_at >= NOW() - INTERVAL '24 hours') as campaigns_today,
                (SELECT COUNT(*) FROM submissions WHERE created_at >= NOW() - INTERVAL '24 hours') as submissions_today
        """
        )

        result = db.execute(metrics_query).mappings().first() or {}
        metrics_time = (time.time() - metrics_start) * 1000

        logger.database_operation(
            operation="AGGREGATE",
            table="users,campaigns,submissions,websites",
            duration_ms=metrics_time,
            success=True,
            query_type="system_metrics",
        )

        # Calculate derived metrics
        total_users = int(result.get("total_users", 0) or 0)
        active_users = int(result.get("active_users", 0) or 0)
        total_submissions = int(result.get("total_submissions", 0) or 0)
        successful_submissions = int(result.get("successful_submissions", 0) or 0)

        user_activity_rate = (
            (active_users / total_users * 100) if total_users > 0 else 0
        )
        submission_success_rate = (
            (successful_submissions / total_submissions * 100)
            if total_submissions > 0
            else 0
        )

        metrics = {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": int(result.get("verified_users", 0) or 0),
                "inactive": total_users - active_users,
                "admins": int(result.get("admin_users", 0) or 0),
                "new_this_week": int(result.get("new_users_week", 0) or 0),
                "activity_rate": round(user_activity_rate, 2),
            },
            "campaigns": {
                "total": int(result.get("total_campaigns", 0) or 0),
                "active": int(result.get("active_campaigns", 0) or 0),
                "completed": int(result.get("completed_campaigns", 0) or 0),
                "failed": int(result.get("failed_campaigns", 0) or 0),
                "created_today": int(result.get("campaigns_today", 0) or 0),
            },
            "submissions": {
                "total": total_submissions,
                "successful": successful_submissions,
                "failed": int(result.get("failed_submissions", 0) or 0),
                "pending": int(result.get("pending_submissions", 0) or 0),
                "with_captcha": int(result.get("captcha_submissions", 0) or 0),
                "success_rate": round(submission_success_rate, 2),
                "today": int(result.get("submissions_today", 0) or 0),
            },
            "websites": {
                "total": int(result.get("total_websites", 0) or 0),
                "with_forms": int(result.get("websites_with_forms", 0) or 0),
                "with_captcha": int(result.get("websites_with_captcha", 0) or 0),
            },
            "system": {
                "status": "healthy",
                "uptime": "running",
                "query_time_ms": round(metrics_time, 2),
            },
        }

        logger.performance_metric(
            name="system_metrics_query_time", value=metrics_time, unit="ms"
        )

        logger.info(
            f"System metrics retrieved",
            context={
                "admin_id": str(current_user.id),
                "query_time_ms": metrics_time,
                "total_users": total_users,
                "total_campaigns": metrics["campaigns"]["total"],
                "total_submissions": total_submissions,
            },
        )

        return metrics

    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={"endpoint": "/admin/metrics", "admin_id": str(current_user.id)},
        )
        return {
            "users": {
                "total": 0,
                "active": 0,
                "verified": 0,
                "inactive": 0,
                "admins": 0,
                "new_this_week": 0,
                "activity_rate": 0,
            },
            "campaigns": {
                "total": 0,
                "active": 0,
                "completed": 0,
                "failed": 0,
                "created_today": 0,
            },
            "submissions": {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "pending": 0,
                "with_captcha": 0,
                "success_rate": 0,
                "today": 0,
            },
            "websites": {"total": 0, "with_forms": 0, "with_captcha": 0},
            "system": {"status": "unknown", "uptime": "unknown", "error": str(e)},
        }
