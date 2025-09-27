# app/api/websites.py - Website management API with comprehensive logging
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.log_service import LogService as ApplicationInsightsLogger
from app.logging import get_logger, log_function, log_exceptions
from app.logging.core import request_id_var, user_id_var, campaign_id_var

# Initialize structured logger
logger = get_logger(__name__)

router = APIRouter(prefix="/api/websites", tags=["websites"], redirect_slashes=False)


class WebsiteResponse(BaseModel):
    id: str
    campaign_id: Optional[str]
    domain: Optional[str]
    contact_url: Optional[str]
    form_detected: Optional[bool]
    form_type: Optional[str]
    form_labels: Optional[List[str]]
    form_field_count: Optional[int]
    has_captcha: Optional[bool]
    captcha_type: Optional[str]
    form_name_variants: Optional[List[str]]
    status: Optional[str]
    failure_reason: Optional[str]
    requires_proxy: Optional[bool]
    proxy_block_type: Optional[str]
    last_proxy_used: Optional[str]
    captcha_difficulty: Optional[str]
    captcha_solution_time: Optional[int]
    captcha_metadata: Optional[Dict[str, Any]]
    form_field_types: Optional[Dict[str, Any]]
    form_field_options: Optional[Dict[str, Any]]
    question_answer_fields: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]
    user_id: Optional[str]


class WebsiteCreateRequest(BaseModel):
    campaign_id: str
    domain: str = Field(..., min_length=1, max_length=255)
    contact_url: str = Field(..., min_length=1)


class WebsiteUpdateRequest(BaseModel):
    domain: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_url: Optional[str] = Field(None, min_length=1)
    form_detected: Optional[bool] = None
    form_type: Optional[str] = Field(None, max_length=100)
    has_captcha: Optional[bool] = None
    captcha_type: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(
        None, pattern="^(pending|processing|completed|failed)$"
    )
    failure_reason: Optional[str] = None


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


@router.post("/", response_model=WebsiteResponse)
@log_function("create_website")
def create_website(
    request: Request,
    website_data: WebsiteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new website"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))
    campaign_id_var.set(website_data.campaign_id)

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(
        user_id=str(current_user.id), campaign_id=website_data.campaign_id
    )

    client_ip = get_client_ip(request)
    website_id = str(uuid.uuid4())

    logger.info(
        "Website creation started",
        context={
            "user_id": str(current_user.id),
            "campaign_id": website_data.campaign_id,
            "website_id": website_id,
            "client_ip": client_ip,
            "domain": website_data.domain,
            "contact_url": website_data.contact_url,
        },
    )

    try:
        # Verify campaign belongs to user
        campaign_check = text(
            """
            SELECT id FROM campaigns 
            WHERE id = :campaign_id AND user_id = :user_id
        """
        )

        campaign_exists = (
            db.execute(
                campaign_check,
                {
                    "campaign_id": website_data.campaign_id,
                    "user_id": str(current_user.id),
                },
            )
            .mappings()
            .first()
        )

        if not campaign_exists:
            logger.warning(
                "Campaign not found for website creation",
                context={
                    "user_id": str(current_user.id),
                    "campaign_id": website_data.campaign_id,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )

        create_start = time.time()

        # Create website record
        insert_query = text(
            """
            INSERT INTO websites (
                id, campaign_id, user_id, domain, contact_url, status, 
                form_detected, has_captcha, created_at, updated_at
            ) VALUES (
                :id, :campaign_id, :user_id, :domain, :contact_url, 'pending',
                false, false, :created_at, :updated_at
            )
        """
        )

        params = {
            "id": website_id,
            "campaign_id": website_data.campaign_id,
            "user_id": str(current_user.id),
            "domain": website_data.domain.strip(),
            "contact_url": website_data.contact_url.strip(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        db.execute(insert_query, params)
        db.commit()

        create_time = (time.time() - create_start) * 1000

        logger.database_operation(
            operation="INSERT",
            table="websites",
            duration_ms=create_time,
            affected_rows=1,
            success=True,
        )

        # Fetch the created website
        select_query = text(
            """
            SELECT * FROM websites WHERE id = :website_id
        """
        )

        website_result = (
            db.execute(select_query, {"website_id": website_id}).mappings().first()
        )

        # Convert to response model
        website_dict = dict(website_result)
        for key, value in website_dict.items():
            if hasattr(value, "isoformat"):
                website_dict[key] = value.isoformat()

        logger.info(
            "Website created successfully",
            context={
                "user_id": str(current_user.id),
                "campaign_id": website_data.campaign_id,
                "website_id": website_id,
                "domain": website_data.domain,
                "create_duration_ms": create_time,
            },
        )

        # Track business events
        app_logger.track_business_event(
            event_name="website_created",
            properties={
                "website_id": website_id,
                "campaign_id": website_data.campaign_id,
                "domain": website_data.domain,
                "user_id": str(current_user.id),
            },
            metrics={"create_time_ms": create_time},
        )

        return WebsiteResponse(**website_dict)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()

        logger.error(
            "Database error during website creation",
            context={
                "user_id": str(current_user.id),
                "campaign_id": website_data.campaign_id,
                "website_id": website_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

        app_logger.track_exception(e, handled=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create website",
        )


@router.get("/", response_model=List[WebsiteResponse])
@log_function("get_websites")
def get_websites(
    request: Request,
    campaign_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get websites for the current user"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))
    if campaign_id:
        campaign_id_var.set(campaign_id)

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id), campaign_id=campaign_id)

    client_ip = get_client_ip(request)

    logger.info(
        "Websites list request started",
        context={
            "user_id": str(current_user.id),
            "client_ip": client_ip,
            "campaign_id": campaign_id,
            "status_filter": status_filter,
            "page": page,
            "page_size": page_size,
        },
    )

    try:
        query_start = time.time()

        # Build query with filters
        where_parts = ["user_id = :user_id"]
        params = {"user_id": str(current_user.id)}

        if campaign_id:
            where_parts.append("campaign_id = :campaign_id")
            params["campaign_id"] = campaign_id

        if status_filter:
            where_parts.append("status = :status")
            params["status"] = status_filter

        where_clause = " AND ".join(where_parts)

        # Count query
        count_query = text(
            f"""
            SELECT COUNT(*) FROM websites WHERE {where_clause}
        """
        )

        total = db.execute(count_query, params).scalar() or 0

        # Data query
        data_query = text(
            f"""
            SELECT * FROM websites 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        )

        params.update({"limit": page_size, "offset": (page - 1) * page_size})

        websites_result = db.execute(data_query, params).mappings().all()
        query_time = (time.time() - query_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="websites",
            duration_ms=query_time,
            affected_rows=len(websites_result),
            success=True,
        )

        # Convert results
        websites = []
        for website in websites_result:
            website_dict = dict(website)
            for key, value in website_dict.items():
                if hasattr(value, "isoformat"):
                    website_dict[key] = value.isoformat()
            websites.append(WebsiteResponse(**website_dict))

        logger.info(
            "Websites retrieved successfully",
            context={
                "user_id": str(current_user.id),
                "websites_found": len(websites),
                "total_websites": total,
                "query_duration_ms": query_time,
                "page": page,
                "page_size": page_size,
            },
        )

        # Track metrics
        app_logger.track_metric(
            name="websites_query_performance",
            value=query_time,
            properties={
                "result_count": len(websites),
                "total_count": total,
                "has_campaign_filter": bool(campaign_id),
                "has_status_filter": bool(status_filter),
            },
        )

        return websites

    except SQLAlchemyError as e:
        logger.error(
            "Database error retrieving websites",
            context={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

        app_logger.track_exception(e, handled=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve websites",
        )


@router.get("/{website_id}", response_model=WebsiteResponse)
@log_function("get_website")
def get_website(
    website_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific website by ID"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    logger.info(
        "Website details request started",
        context={
            "user_id": str(current_user.id),
            "website_id": website_id,
            "client_ip": client_ip,
        },
    )

    try:
        query_start = time.time()

        select_query = text(
            """
            SELECT * FROM websites 
            WHERE id = :website_id AND user_id = :user_id
        """
        )

        website_result = (
            db.execute(
                select_query,
                {"website_id": website_id, "user_id": str(current_user.id)},
            )
            .mappings()
            .first()
        )

        query_time = (time.time() - query_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="websites",
            duration_ms=query_time,
            affected_rows=1 if website_result else 0,
            success=True,
        )

        if not website_result:
            logger.warning(
                "Website not found",
                context={"user_id": str(current_user.id), "website_id": website_id},
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Website not found"
            )

        # Convert to response model
        website_dict = dict(website_result)
        for key, value in website_dict.items():
            if hasattr(value, "isoformat"):
                website_dict[key] = value.isoformat()

        # Set campaign context if available
        if website_dict.get("campaign_id"):
            campaign_id_var.set(website_dict["campaign_id"])

        logger.info(
            "Website details retrieved successfully",
            context={
                "user_id": str(current_user.id),
                "website_id": website_id,
                "campaign_id": website_dict.get("campaign_id"),
                "domain": website_dict.get("domain"),
                "status": website_dict.get("status"),
                "query_duration_ms": query_time,
            },
        )

        # Track business event
        app_logger.track_user_action(
            action="view_website",
            target=website_id,
            properties={
                "domain": website_dict.get("domain"),
                "status": website_dict.get("status"),
                "has_captcha": website_dict.get("has_captcha"),
            },
        )

        return WebsiteResponse(**website_dict)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(
            "Database error retrieving website",
            context={
                "user_id": str(current_user.id),
                "website_id": website_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

        app_logger.track_exception(e, handled=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve website",
        )


@router.put("/{website_id}", response_model=WebsiteResponse)
@log_function("update_website")
def update_website(
    website_id: str,
    website_data: WebsiteUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a website"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    # Track what fields are being updated
    updated_data = website_data.model_dump(exclude_unset=True)
    updated_fields = [k for k, v in updated_data.items() if v is not None]

    logger.info(
        "Website update request started",
        context={
            "user_id": str(current_user.id),
            "website_id": website_id,
            "client_ip": client_ip,
            "fields_to_update": updated_fields,
            "update_count": len(updated_fields),
        },
    )

    try:
        # First, verify website exists and belongs to user
        check_query = text(
            """
            SELECT campaign_id, status, domain FROM websites 
            WHERE id = :website_id AND user_id = :user_id
        """
        )

        existing_website = (
            db.execute(
                check_query, {"website_id": website_id, "user_id": str(current_user.id)}
            )
            .mappings()
            .first()
        )

        if not existing_website:
            logger.warning(
                "Website not found for update",
                context={"user_id": str(current_user.id), "website_id": website_id},
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Website not found"
            )

        # Set campaign context
        if existing_website["campaign_id"]:
            campaign_id_var.set(existing_website["campaign_id"])

        # Build update query
        update_start = time.time()
        update_parts = []
        params = {"website_id": website_id, "user_id": str(current_user.id)}

        for field, value in updated_data.items():
            if value is not None:
                update_parts.append(f"{field} = :{field}")
                if isinstance(value, str):
                    params[field] = value.strip()
                else:
                    params[field] = value

        if update_parts:
            update_parts.append("updated_at = :updated_at")
            params["updated_at"] = datetime.utcnow()

            update_query = text(
                f"""
                UPDATE websites 
                SET {', '.join(update_parts)}
                WHERE id = :website_id AND user_id = :user_id
            """
            )

            db.execute(update_query, params)
            db.commit()

        update_time = (time.time() - update_start) * 1000

        logger.database_operation(
            operation="UPDATE",
            table="websites",
            duration_ms=update_time,
            affected_rows=1,
            success=True,
        )

        # Fetch updated website
        select_query = text(
            """
            SELECT * FROM websites 
            WHERE id = :website_id AND user_id = :user_id
        """
        )

        updated_website = (
            db.execute(
                select_query,
                {"website_id": website_id, "user_id": str(current_user.id)},
            )
            .mappings()
            .first()
        )

        # Convert to response model
        website_dict = dict(updated_website)
        for key, value in website_dict.items():
            if hasattr(value, "isoformat"):
                website_dict[key] = value.isoformat()

        logger.info(
            "Website updated successfully",
            context={
                "user_id": str(current_user.id),
                "website_id": website_id,
                "fields_updated": updated_fields,
                "update_duration_ms": update_time,
            },
        )

        # Track business event
        app_logger.track_business_event(
            event_name="website_updated",
            properties={
                "website_id": website_id,
                "domain": existing_website["domain"],
                "fields_updated": updated_fields,
                "previous_status": existing_website["status"],
                "new_status": website_dict.get("status"),
            },
            metrics={
                "update_time_ms": update_time,
                "fields_changed": len(updated_fields),
            },
        )

        return WebsiteResponse(**website_dict)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()

        logger.error(
            "Database error updating website",
            context={
                "user_id": str(current_user.id),
                "website_id": website_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "fields_being_updated": updated_fields,
            },
        )

        app_logger.track_exception(e, handled=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update website",
        )


@router.delete("/{website_id}")
@log_function("delete_website")
def delete_website(
    website_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a website"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id))

    client_ip = get_client_ip(request)

    logger.info(
        "Website deletion request started",
        context={
            "user_id": str(current_user.id),
            "website_id": website_id,
            "client_ip": client_ip,
        },
    )

    try:
        delete_start = time.time()

        # First, verify website exists and get details for logging
        check_query = text(
            """
            SELECT domain, status, campaign_id FROM websites 
            WHERE id = :website_id AND user_id = :user_id
        """
        )

        existing_website = (
            db.execute(
                check_query, {"website_id": website_id, "user_id": str(current_user.id)}
            )
            .mappings()
            .first()
        )

        if not existing_website:
            logger.warning(
                "Website not found for deletion",
                context={"user_id": str(current_user.id), "website_id": website_id},
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Website not found"
            )

        # Set campaign context
        if existing_website["campaign_id"]:
            campaign_id_var.set(existing_website["campaign_id"])

        # Delete related submissions first
        delete_submissions_query = text(
            """
            DELETE FROM submissions WHERE website_id = :website_id
        """
        )
        submissions_deleted = db.execute(
            delete_submissions_query, {"website_id": website_id}
        ).rowcount

        # Delete the website
        delete_query = text(
            """
            DELETE FROM websites 
            WHERE id = :website_id AND user_id = :user_id
        """
        )

        result = db.execute(
            delete_query, {"website_id": website_id, "user_id": str(current_user.id)}
        )

        db.commit()
        delete_time = (time.time() - delete_start) * 1000

        logger.database_operation(
            operation="DELETE",
            table="websites",
            duration_ms=delete_time,
            affected_rows=result.rowcount,
            success=True,
        )

        logger.info(
            "Website deleted successfully",
            context={
                "user_id": str(current_user.id),
                "website_id": website_id,
                "domain": existing_website["domain"],
                "submissions_deleted": submissions_deleted,
                "delete_duration_ms": delete_time,
            },
        )

        # Track business event
        app_logger.track_business_event(
            event_name="website_deleted",
            properties={
                "website_id": website_id,
                "domain": existing_website["domain"],
                "status": existing_website["status"],
                "campaign_id": existing_website["campaign_id"],
                "had_submissions": submissions_deleted > 0,
            },
            metrics={
                "delete_time_ms": delete_time,
                "submissions_deleted": submissions_deleted,
            },
        )

        return {"message": "Website deleted successfully"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()

        logger.error(
            "Database error deleting website",
            context={
                "user_id": str(current_user.id),
                "website_id": website_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

        app_logger.track_exception(e, handled=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete website",
        )


@router.get("/campaign/{campaign_id}/stats")
@log_function("get_campaign_website_stats")
def get_campaign_website_stats(
    campaign_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get website statistics for a campaign"""
    # Set context variables for structured logging
    user_id_var.set(str(current_user.id))
    campaign_id_var.set(campaign_id)

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(current_user.id), campaign_id=campaign_id)

    client_ip = get_client_ip(request)

    logger.info(
        "Campaign website stats request started",
        context={
            "user_id": str(current_user.id),
            "campaign_id": campaign_id,
            "client_ip": client_ip,
        },
    )

    try:
        stats_start = time.time()

        # Verify campaign belongs to user
        campaign_check = text(
            """
            SELECT id FROM campaigns 
            WHERE id = :campaign_id AND user_id = :user_id
        """
        )

        campaign_exists = (
            db.execute(
                campaign_check,
                {"campaign_id": campaign_id, "user_id": str(current_user.id)},
            )
            .mappings()
            .first()
        )

        if not campaign_exists:
            logger.warning(
                "Campaign not found for stats",
                context={"user_id": str(current_user.id), "campaign_id": campaign_id},
            )

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )

        # Get website statistics
        stats_query = text(
            """
            SELECT 
                status,
                COUNT(*) as count,
                COUNT(CASE WHEN form_detected = true THEN 1 END) as with_forms,
                COUNT(CASE WHEN has_captcha = true THEN 1 END) as with_captcha,
                COUNT(CASE WHEN requires_proxy = true THEN 1 END) as requires_proxy
            FROM websites 
            WHERE campaign_id = :campaign_id
            GROUP BY status
            
            UNION ALL
            
            SELECT 
                'total' as status,
                COUNT(*) as count,
                COUNT(CASE WHEN form_detected = true THEN 1 END) as with_forms,
                COUNT(CASE WHEN has_captcha = true THEN 1 END) as with_captcha,
                COUNT(CASE WHEN requires_proxy = true THEN 1 END) as requires_proxy
            FROM websites 
            WHERE campaign_id = :campaign_id
        """
        )

        stats_result = (
            db.execute(stats_query, {"campaign_id": campaign_id}).mappings().all()
        )
        stats_time = (time.time() - stats_start) * 1000

        logger.database_operation(
            operation="AGGREGATE",
            table="websites",
            duration_ms=stats_time,
            success=True,
        )

        # Process results
        stats = {}
        for row in stats_result:
            stats[row["status"]] = {
                "count": row["count"],
                "with_forms": row["with_forms"],
                "with_captcha": row["with_captcha"],
                "requires_proxy": row["requires_proxy"],
            }

        logger.info(
            "Campaign website stats retrieved",
            context={
                "user_id": str(current_user.id),
                "campaign_id": campaign_id,
                "total_websites": stats.get("total", {}).get("count", 0),
                "stats_duration_ms": stats_time,
            },
        )

        # Track business event
        app_logger.track_business_event(
            event_name="campaign_website_stats_viewed",
            properties={"campaign_id": campaign_id, "user_id": str(current_user.id)},
            metrics={
                "query_time_ms": stats_time,
                "total_websites": stats.get("total", {}).get("count", 0),
            },
        )

        return {"stats": stats}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(
            "Database error retrieving website stats",
            context={
                "user_id": str(current_user.id),
                "campaign_id": campaign_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

        app_logger.track_exception(e, handled=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve website statistics",
        )
