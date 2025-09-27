# app/api/users.py - Enhanced with comprehensive logging
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Union

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, File, UploadFile

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.log_service import LogService as ApplicationInsightsLogger
from app.logging import get_logger, log_function, log_exceptions
from app.logging.core import request_id_var, user_id_var

# Initialize structured logger
logger = get_logger(__name__)

router = APIRouter(tags=["users"], redirect_slashes=False)


class ProfileUpdateRequest(BaseModel):
    # Basic Information
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)

    # Company Information
    company_name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    website_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)

    # Location Information
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=100)

    # Contact Preferences
    preferred_language: Optional[str] = Field(None, max_length=10)
    language: Optional[str] = Field(None, max_length=50)
    preferred_contact: Optional[str] = Field(None, max_length=100)
    best_time_to_contact: Optional[str] = Field(None, max_length=100)

    # Message Defaults
    subject: Optional[str] = Field(None, max_length=500)
    message: Optional[str] = Field(None)

    # Business Information
    product_interest: Optional[str] = Field(None, max_length=255)
    budget_range: Optional[str] = Field(None, max_length=100)
    referral_source: Optional[str] = Field(None, max_length=255)
    contact_source: Optional[str] = Field(None, max_length=255)
    is_existing_customer: Optional[bool] = Field(None)

    # Additional Fields
    notes: Optional[str] = Field(None)
    form_custom_field_1: Optional[str] = Field(None, max_length=500)
    form_custom_field_2: Optional[str] = Field(None, max_length=500)
    form_custom_field_3: Optional[str] = Field(None, max_length=500)

    # Death By Captcha Credentials
    dbc_username: Optional[str] = Field(None, max_length=255)
    dbc_password: Optional[str] = Field(None, max_length=255)


class UserProfileResponse(BaseModel):
    user: Dict[str, Any]
    profile: Dict[str, Any]


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers with logging"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        logger.debug(f"Client IP extracted from X-Forwarded-For: {ip}")
        return ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        logger.debug(f"Client IP extracted from X-Real-IP: {real_ip}")
        return real_ip

    if request and request.client:
        ip = request.client.host
        logger.debug(f"Client IP extracted from request.client: {ip}")
        return ip

    logger.warning("Unable to determine client IP address")
    return "unknown"


def _get_role_string(user: User) -> str:
    """Helper function to extract role as string"""
    role = getattr(user, "role", "user")
    if hasattr(role, "value"):
        return str(role.value)
    return str(role)


@router.get("/profile", response_model=UserProfileResponse)
@log_function("get_user_profile")
def get_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user profile combining base user data and extended profile information"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    logger.info(
        "Profile retrieval request started",
        context={
            "user_id": str(current_user.id),
            "client_ip": client_ip,
            "user_email": current_user.email,
        },
    )

    try:
        profile_start = time.time()

        # Build base user data
        base = {
            "id": str(current_user.id),
            "email": current_user.email,
            "first_name": getattr(current_user, "first_name", None),
            "last_name": getattr(current_user, "last_name", None),
            "role": _get_role_string(current_user),
            "is_active": getattr(current_user, "is_active", True),
            "is_verified": getattr(current_user, "is_verified", True),
            "profile_image_url": getattr(current_user, "profile_image_url", None),
            "created_at": (
                current_user.created_at.isoformat()
                if hasattr(current_user, "created_at") and current_user.created_at
                else None
            ),
            "updated_at": (
                current_user.updated_at.isoformat()
                if hasattr(current_user, "updated_at") and current_user.updated_at
                else None
            ),
        }

        # Get extended profile information including DBC credentials
        profile_query_start = time.time()
        profile_query = text(
            """
            SELECT
                up.phone_number, up.company_name, 
                up.job_title, up.website_url, up.linkedin_url, up.industry, 
                up.city, up.state, up.zip_code, up.country, up.region, 
                up.timezone, up.subject, up.message, up.product_interest,
                up.budget_range, up.referral_source, up.preferred_contact, 
                up.best_time_to_contact, up.contact_source, up.is_existing_customer, 
                up.language, up.preferred_language, up.notes, 
                up.form_custom_field_1, up.form_custom_field_2, up.form_custom_field_3,
                up.dbc_username, 
                CASE 
                    WHEN up.dbc_password IS NOT NULL AND up.dbc_password != '' 
                    THEN '********' 
                    ELSE NULL 
                END as dbc_password_masked,
                CASE 
                    WHEN up.dbc_username IS NOT NULL AND up.dbc_password IS NOT NULL 
                    THEN true 
                    ELSE false 
                END as has_dbc_credentials,
                up.created_at, up.updated_at
            FROM user_profiles up
            WHERE up.user_id = :uid
            LIMIT 1
        """
        )

        profile_result = (
            db.execute(profile_query, {"uid": str(current_user.id)}).mappings().first()
        )
        profile_query_time = (time.time() - profile_query_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="user_profiles",
            duration_ms=profile_query_time,
            affected_rows=1 if profile_result else 0,
            success=True,
        )

        profile = dict(profile_result) if profile_result else {}

        # Convert datetime objects to ISO strings in profile
        for key, value in profile.items():
            if hasattr(value, "isoformat"):
                profile[key] = value.isoformat()

        # Calculate profile completeness
        populated_fields = len([v for v in profile.values() if v])
        total_fields = len(profile) if profile else 1
        completeness_percent = (populated_fields / total_fields) * 100

        # Add CAPTCHA status if DBC credentials exist
        captcha_enabled = profile.get("has_dbc_credentials", False)
        if captcha_enabled:
            profile["captcha_enabled"] = True

        payload = {"user": base, "profile": profile}
        total_time = (time.time() - profile_start) * 1000

        logger.info(
            "Profile retrieved successfully",
            context={
                "user_id": str(current_user.id),
                "has_extended_profile": bool(profile),
                "profile_completeness_percent": completeness_percent,
                "has_captcha_credentials": captcha_enabled,
                "total_duration_ms": total_time,
            },
        )

        # Track detailed metrics
        app_logger.track_metric(
            name="profile_completeness",
            value=completeness_percent,
            properties={
                "user_id": str(current_user.id),
                "has_extended_profile": bool(profile),
                "populated_fields": populated_fields,
                "total_fields": total_fields,
            },
        )

        # Track performance metrics
        app_logger.track_metric(
            name="profile_query_performance",
            value=profile_query_time,
            properties={"user_id": str(current_user.id), "has_profile": bool(profile)},
        )

        # Track business event
        app_logger.track_business_event(
            event_name="profile_retrieved",
            properties={
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "has_extended_profile": bool(profile),
                "has_dbc_credentials": captcha_enabled,
                "profile_fields_populated": populated_fields,
                "user_role": _get_role_string(current_user),
            },
            metrics={
                "query_time_ms": profile_query_time,
                "total_time_ms": total_time,
                "completeness_percent": completeness_percent,
            },
        )

        # Track user action
        app_logger.track_user_action(
            action="view_profile",
            target="user_profile",
            properties={
                "user_id": str(current_user.id),
                "ip": client_ip,
                "profile_exists": bool(profile),
            },
        )

        return payload

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Database error retrieving profile",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )
    except Exception as e:
        logger.error(
            "Unexpected error retrieving profile",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile",
        )


@router.put("/profile")
@log_function("update_user_profile")
def update_profile(
    request: Request,
    profile_data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user profile information including DBC credentials"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    # Track what fields are being updated
    updated_data = profile_data.model_dump(exclude_unset=True)
    updated_fields = [k for k, v in updated_data.items() if v is not None]

    # Check if DBC credentials are being updated
    updating_dbc = "dbc_username" in updated_fields or "dbc_password" in updated_fields

    logger.info(
        "Profile update request started",
        context={
            "user_id": str(current_user.id),
            "client_ip": client_ip,
            "fields_to_update": updated_fields,
            "update_count": len(updated_fields),
            "updating_dbc_credentials": updating_dbc,
            "user_email": current_user.email,
        },
    )

    try:
        update_start = time.time()

        # Update base user fields if provided
        user_updated = False
        user_changes = {}
        user_update_start = time.time()

        if profile_data.first_name is not None:
            old_value = getattr(current_user, "first_name", None)
            current_user.first_name = profile_data.first_name.strip()
            user_updated = True
            user_changes["first_name"] = {
                "old": old_value,
                "new": current_user.first_name,
            }

        if profile_data.last_name is not None:
            old_value = getattr(current_user, "last_name", None)
            current_user.last_name = profile_data.last_name.strip()
            user_updated = True
            user_changes["last_name"] = {
                "old": old_value,
                "new": current_user.last_name,
            }

        user_update_time = 0
        if user_updated:
            current_user.updated_at = datetime.utcnow()
            db.add(current_user)
            user_update_time = (time.time() - user_update_start) * 1000

            logger.database_operation(
                operation="UPDATE",
                table="users",
                duration_ms=user_update_time,
                affected_rows=1,
                success=True,
            )

        # Check if user profile exists
        profile_check_start = time.time()
        profile_exists_query = text(
            """
            SELECT COUNT(*) FROM user_profiles WHERE user_id = :uid
        """
        )
        profile_exists = (
            db.execute(profile_exists_query, {"uid": str(current_user.id)}).scalar() > 0
        )
        profile_check_time = (time.time() - profile_check_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="user_profiles",
            duration_ms=profile_check_time,
            success=True,
        )

        # Prepare profile data (excluding user table fields)
        profile_fields = {}
        for field, value in updated_data.items():
            if value is not None and field not in ["first_name", "last_name"]:
                # Don't strip password fields
                if field == "dbc_password":
                    profile_fields[field] = value
                else:
                    profile_fields[field] = (
                        value.strip() if isinstance(value, str) else value
                    )

        profile_update_time = 0
        if profile_fields:
            profile_update_start = time.time()

            if profile_exists:
                # Update existing profile
                update_parts = []
                params = {"uid": str(current_user.id)}

                for field, value in profile_fields.items():
                    update_parts.append(f"{field} = :{field}")
                    params[field] = value

                if update_parts:
                    params["updated_at"] = datetime.utcnow()
                    update_parts.append("updated_at = :updated_at")

                    update_query = text(
                        f"""
                        UPDATE user_profiles 
                        SET {', '.join(update_parts)}
                        WHERE user_id = :uid
                    """
                    )
                    db.execute(update_query, params)
            else:
                # Create new profile
                fields = list(profile_fields.keys()) + [
                    "user_id",
                    "created_at",
                    "updated_at",
                ]
                placeholders = [f":{field}" for field in fields]

                profile_fields.update(
                    {
                        "user_id": str(current_user.id),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                )

                insert_query = text(
                    f"""
                    INSERT INTO user_profiles ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                """
                )
                db.execute(insert_query, profile_fields)

            profile_update_time = (time.time() - profile_update_start) * 1000

            logger.database_operation(
                operation="UPDATE" if profile_exists else "INSERT",
                table="user_profiles",
                duration_ms=profile_update_time,
                affected_rows=1,
                success=True,
            )

        db.commit()
        total_update_time = (time.time() - update_start) * 1000

        logger.info(
            "Profile updated successfully",
            context={
                "user_id": str(current_user.id),
                "fields_updated": updated_fields,
                "user_fields_changed": list(user_changes.keys()),
                "profile_fields_changed": list(profile_fields.keys()),
                "profile_created": not profile_exists and bool(profile_fields),
                "total_duration_ms": total_update_time,
            },
        )

        # Track detailed business event
        app_logger.track_business_event(
            event_name="profile_updated",
            properties={
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "fields_updated": updated_fields,
                "user_fields_changed": list(user_changes.keys()),
                "profile_fields_changed": list(profile_fields.keys()),
                "profile_created": not profile_exists and bool(profile_fields),
                "dbc_credentials_updated": updating_dbc,
                "ip_address": client_ip,
            },
            metrics={
                "user_update_time_ms": user_update_time,
                "profile_update_time_ms": profile_update_time,
                "total_update_time_ms": total_update_time,
                "fields_updated_count": len(updated_fields),
                "profile_check_time_ms": profile_check_time,
            },
        )

        # Log DBC update specifically for security monitoring
        if updating_dbc:
            app_logger.track_security_event(
                event_name="dbc_credentials_updated",
                user_id=str(current_user.id),
                ip_address=client_ip,
                success=True,
                details={
                    "has_username": bool(profile_data.dbc_username),
                    "has_password": bool(profile_data.dbc_password),
                    "username_changed": "dbc_username" in profile_fields,
                    "password_changed": "dbc_password" in profile_fields,
                },
            )

            logger.info(
                "DBC credentials updated",
                context={
                    "user_id": str(current_user.id),
                    "has_username": bool(profile_data.dbc_username),
                    "has_password": bool(profile_data.dbc_password),
                    "client_ip": client_ip,
                },
            )

        # Track user action
        app_logger.track_user_action(
            action="update_profile",
            target="user_profile",
            properties={
                "user_id": str(current_user.id),
                "fields_updated": updated_fields,
                "field_count": len(updated_fields),
                "updating_dbc": updating_dbc,
                "ip": client_ip,
            },
        )

        # Track performance metrics
        app_logger.track_metric(
            name="profile_update_performance",
            value=total_update_time,
            properties={
                "fields_count": len(updated_fields),
                "profile_existed": profile_exists,
                "user_updated": user_updated,
            },
        )

        return {
            "success": True,
            "message": "Profile updated successfully",
            "fields_updated": updated_fields,
            "update_summary": {
                "user_fields": list(user_changes.keys()),
                "profile_fields": list(profile_fields.keys()),
                "profile_created": not profile_exists and bool(profile_fields),
            },
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Database error updating profile",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "fields_being_updated": updated_fields,
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )
    except Exception as e:
        logger.error(
            "Unexpected error updating profile",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "fields_being_updated": updated_fields,
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile",
        )


@router.post("/upload-avatar")
async def upload_avatar(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> dict:  # Explicit return type
    """Upload user avatar/profile image"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Validate file size (5MB limit)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")

    try:
        # Read file content
        file_content = await file.read()
        file_extension = (
            file.filename.split(".")[-1]
            if file.filename and "." in file.filename
            else "jpg"
        )
        file_name = f"{current_user.id}_{int(time.time())}.{file_extension}"

        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file locally
        file_path = os.path.join(upload_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Generate URL
        profile_image_url = f"/static/{upload_dir}/{file_name}"

        # Update user record
        current_user.profile_image_url = profile_image_url
        current_user.updated_at = datetime.utcnow()
        db.add(current_user)
        db.commit()

        return {
            "profile_image_url": profile_image_url,
            "success": True,
            "file_info": {
                "original_name": file.filename,
                "saved_name": file_name,
                "size_bytes": len(file_content),
                "content_type": file.content_type,
            },
        }

    except Exception as e:
        db.rollback()
        app_logger.track_exception(e, handled=True)
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.get("/stats")
@log_function("get_user_stats")
def get_user_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user statistics and metrics"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    logger.info(
        "User stats request started",
        context={"user_id": str(current_user.id), "client_ip": client_ip},
    )

    try:
        stats_start = time.time()

        # Get campaign statistics
        campaigns_query = text(
            """
            SELECT 
                COUNT(*) as total_campaigns,
                COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_campaigns,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_campaigns,
                COUNT(CASE WHEN status = 'DRAFT' THEN 1 END) as draft_campaigns,
                COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_campaigns
            FROM campaigns WHERE user_id = :user_id
        """
        )

        campaigns_result = (
            db.execute(campaigns_query, {"user_id": str(current_user.id)})
            .mappings()
            .first()
        )

        # Get submission statistics
        submissions_query = text(
            """
            SELECT 
                COUNT(*) as total_submissions,
                COUNT(CASE WHEN status = 'successful' THEN 1 END) as successful_submissions,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_submissions,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_submissions
            FROM submissions s
            JOIN campaigns c ON s.campaign_id = c.id
            WHERE c.user_id = :user_id
        """
        )

        submissions_result = (
            db.execute(submissions_query, {"user_id": str(current_user.id)})
            .mappings()
            .first()
        )

        stats_time = (time.time() - stats_start) * 1000

        logger.database_operation(
            operation="AGGREGATE",
            table="campaigns,submissions",
            duration_ms=stats_time,
            success=True,
        )

        # Build response
        stats = {
            "user_info": {
                "id": str(current_user.id),
                "email": current_user.email,
                "role": _get_role_string(current_user),
                "is_active": getattr(current_user, "is_active", True),
                "created_at": (
                    current_user.created_at.isoformat()
                    if hasattr(current_user, "created_at") and current_user.created_at
                    else None
                ),
            },
            "campaigns": dict(campaigns_result) if campaigns_result else {},
            "submissions": dict(submissions_result) if submissions_result else {},
            "calculated_metrics": {},
        }

        # Calculate additional metrics
        total_campaigns = stats["campaigns"].get("total_campaigns", 0)
        total_submissions = stats["submissions"].get("total_submissions", 0)
        successful_submissions = stats["submissions"].get("successful_submissions", 0)

        if total_submissions > 0:
            success_rate = (successful_submissions / total_submissions) * 100
            stats["calculated_metrics"]["overall_success_rate"] = round(success_rate, 2)

        if total_campaigns > 0:
            stats["calculated_metrics"]["avg_submissions_per_campaign"] = round(
                total_submissions / total_campaigns, 2
            )

        logger.info(
            "User stats retrieved successfully",
            context={
                "user_id": str(current_user.id),
                "total_campaigns": total_campaigns,
                "total_submissions": total_submissions,
                "success_rate": stats["calculated_metrics"].get(
                    "overall_success_rate", 0
                ),
                "stats_duration_ms": stats_time,
            },
        )

        # Track business event
        app_logger.track_business_event(
            event_name="user_stats_retrieved",
            properties={
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "ip_address": client_ip,
            },
            metrics={
                "query_time_ms": stats_time,
                "total_campaigns": total_campaigns,
                "total_submissions": total_submissions,
                "success_rate": stats["calculated_metrics"].get(
                    "overall_success_rate", 0
                ),
            },
        )

        # Track user action
        app_logger.track_user_action(
            action="view_stats",
            target="user_stats",
            properties={"user_id": str(current_user.id), "ip": client_ip},
        )

        return stats

    except SQLAlchemyError as e:
        logger.error(
            "Database error retrieving user stats",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics",
        )
    except Exception as e:
        logger.error(
            "Unexpected error retrieving user stats",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics",
        )
