# app/api/campaigns.py - Complete Fixed Version With Correct Parameter Ordering
import time
import uuid
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal, Union
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks,
    status,
    Request,
    Query,
    Form,
    File,
    UploadFile,
)
import csv
import io
import asyncio
import threading
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.log_service import LogService as ApplicationInsightsLogger
from app.logging import get_logger, log_function, log_exceptions
from app.logging.core import request_id_var, user_id_var, campaign_id_var
from app.workers.processors.subprocess_runner import start_campaign_processing

# Initialize structured logger
logger = get_logger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"], redirect_slashes=False)


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers with logging"""
    if not request:
        return "unknown"

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        logger.debug(f"Client IP extracted from X-Forwarded-For: {ip}")
        return ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        logger.debug(f"Client IP extracted from X-Real-IP: {real_ip}")
        return real_ip

    if request.client:
        ip = request.client.host
        logger.debug(f"Client IP extracted from request.client: {ip}")
        return ip

    logger.warning("Unable to determine client IP address")
    return "unknown"


# ===========================
# CAMPAIGN CREATION WITH CSV
# ===========================


from app.services.submission_service import SubmissionService
from app.services.csv_parser_service import CSVParserService


@router.post("/start", response_model=None)
@log_function("start_campaign_with_csv")
async def start_campaign_with_csv(
    request: Request,
    name: str = Form(...),
    message: str = Form(...),
    file: UploadFile = File(...),
    proxy: Optional[str] = Form(None),
    use_captcha: bool = Form(False),
    settings: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start campaign with enhanced CSV parsing and submission creation."""
    user_id_var.set(str(user.id))
    campaign_id = str(uuid.uuid4())
    campaign_id_var.set(campaign_id)

    try:
        # Validate file
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Enhanced CSV parsing using your service
        content = await file.read()
        valid_urls, processing_report = await CSVParserService.parse_csv_file(content)

        if processing_report.get("errors"):
            error_details = "; ".join(processing_report["errors"])
            raise HTTPException(
                status_code=400, detail=f"CSV parsing failed: {error_details}"
            )

        if not valid_urls:
            raise HTTPException(
                status_code=400, detail="No valid URLs found in CSV file"
            )

        total_urls = len(valid_urls)
        logger.info(f"Parsed {total_urls} valid URLs from CSV")

        # Create campaign
        now = datetime.utcnow()
        insert_query = text(
            """
            INSERT INTO campaigns (
                id, user_id, name, message, csv_filename, file_name,
                total_urls, total_websites, status, use_captcha, proxy,
                created_at, updated_at, started_at
            ) VALUES (
                :id, :user_id, :name, :message, :csv_filename, :file_name,
                :total_urls, :total_websites, :status, :use_captcha, :proxy,
                :created_at, :updated_at, :started_at
            )
        """
        )

        db.execute(
            insert_query,
            {
                "id": campaign_id,
                "user_id": str(user.id),
                "name": name.strip(),
                "message": message.strip() if message else None,
                "csv_filename": file.filename,
                "file_name": file.filename,
                "total_urls": total_urls,
                "total_websites": total_urls,
                "status": "PROCESSING",
                "use_captcha": use_captcha,
                "proxy": proxy if proxy else None,
                "created_at": now,
                "updated_at": now,
                "started_at": now,
            },
        )

        # Create submissions using your service
        submission_service = SubmissionService(db)
        try:
            submissions, errors = submission_service.bulk_create_submissions(
                user_id=user.id, campaign_id=uuid.UUID(campaign_id), urls=valid_urls
            )

            if errors:
                logger.warning(f"Some submissions had errors: {errors}")

        except Exception as e:
            logger.error(f"Error creating submissions: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create submissions")

        db.commit()

        # Start automation using your integrated system
        try:
            from app.workers.processors.subprocess_runner import (
                start_campaign_processing,
            )

            automation_started = start_campaign_processing(campaign_id, str(user.id))

            if automation_started:
                logger.info("Campaign automation started successfully")
            else:
                logger.error("Failed to start campaign automation")

        except Exception as automation_error:
            logger.error(f"Automation start error: {automation_error}")
            # Mark campaign as failed
            update_query = text(
                """
                UPDATE campaigns 
                SET status = 'FAILED', 
                    error_message = :error_message,
                    updated_at = :updated_at
                WHERE id = :campaign_id
            """
            )
            db.execute(
                update_query,
                {
                    "campaign_id": campaign_id,
                    "error_message": f"Automation failed to start: {str(automation_error)}",
                    "updated_at": datetime.utcnow(),
                },
            )
            db.commit()

        return {
            "success": True,
            "message": "Campaign started successfully",
            "campaign_id": campaign_id,
            "total_urls": total_urls,
            "status": "PROCESSING",
            "automation_started": automation_started,
            "processing_report": {
                "valid_urls": processing_report.get("valid_urls", 0),
                "duplicates_removed": processing_report.get("duplicates_removed", 0),
                "invalid_urls": len(processing_report.get("invalid_urls", [])),
                "success_rate": processing_report.get("statistics", {}).get(
                    "success_rate", 0
                ),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Campaign creation error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start campaign: {str(e)}"
        )


# ===========================
# CAMPAIGN MANAGEMENT ACTIONS
# ===========================


@router.post("/{campaign_id}/start")
@log_function("start_existing_campaign")
def start_existing_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start an existing campaign"""
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    try:
        # Check if campaign exists and belongs to user
        check_query = text(
            "SELECT status FROM campaigns WHERE id = :campaign_id AND user_id = :user_id"
        )
        result = db.execute(
            check_query, {"campaign_id": str(campaign_id), "user_id": str(user.id)}
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if result[0] in ["RUNNING", "PROCESSING"]:
            raise HTTPException(status_code=400, detail="Campaign is already running")

        # Update campaign status
        update_query = text(
            """UPDATE campaigns 
               SET status = 'RUNNING', started_at = :started_at, updated_at = :updated_at
               WHERE id = :campaign_id"""
        )
        now = datetime.utcnow()
        db.execute(
            update_query,
            {"campaign_id": str(campaign_id), "started_at": now, "updated_at": now},
        )
        db.commit()

        return {"success": True, "message": "Campaign started successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to start campaign: {str(e)}"
        )


@router.post("/{campaign_id}/pause")
@log_function("pause_campaign")
def pause_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Pause a running campaign"""
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    try:
        # Update campaign status
        update_query = text(
            """UPDATE campaigns 
               SET status = 'PAUSED', updated_at = :updated_at
               WHERE id = :campaign_id AND user_id = :user_id 
               AND status IN ('RUNNING', 'PROCESSING')"""
        )
        result = db.execute(
            update_query,
            {
                "campaign_id": str(campaign_id),
                "user_id": str(user.id),
                "updated_at": datetime.utcnow(),
            },
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404, detail="Campaign not found or not running"
            )

        db.commit()
        return {"success": True, "message": "Campaign paused successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to pause campaign: {str(e)}"
        )


@router.post("/{campaign_id}/stop")
@log_function("stop_campaign")
def stop_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stop a running campaign"""
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    try:
        # Update campaign status
        update_query = text(
            """UPDATE campaigns 
               SET status = 'STOPPED', updated_at = :updated_at, completed_at = :completed_at
               WHERE id = :campaign_id AND user_id = :user_id 
               AND status IN ('RUNNING', 'PROCESSING', 'PAUSED')"""
        )
        now = datetime.utcnow()
        result = db.execute(
            update_query,
            {
                "campaign_id": str(campaign_id),
                "user_id": str(user.id),
                "updated_at": now,
                "completed_at": now,
            },
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404, detail="Campaign not found or already stopped"
            )

        db.commit()
        return {"success": True, "message": "Campaign stopped successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to stop campaign: {str(e)}"
        )


@router.post("/{campaign_id}/duplicate", response_model=None)
@log_function("duplicate_campaign")
def duplicate_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    request_data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Duplicate an existing campaign"""
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    try:
        # Get original campaign
        select_query = text(
            """SELECT name, message, csv_filename, file_name, use_captcha, proxy
               FROM campaigns WHERE id = :campaign_id AND user_id = :user_id"""
        )
        original = db.execute(
            select_query, {"campaign_id": str(campaign_id), "user_id": str(user.id)}
        ).first()

        if not original:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Create duplicate
        new_campaign_id = str(uuid.uuid4())
        new_name = request_data.get("name", f"{original.name} (Copy)")

        insert_query = text(
            """INSERT INTO campaigns (
                id, user_id, name, message, csv_filename, file_name,
                use_captcha, proxy, status, created_at, updated_at
               ) VALUES (
                :id, :user_id, :name, :message, :csv_filename, :file_name,
                :use_captcha, :proxy, :status, :created_at, :updated_at
               )"""
        )

        now = datetime.utcnow()
        db.execute(
            insert_query,
            {
                "id": new_campaign_id,
                "user_id": str(user.id),
                "name": new_name,
                "message": original.message,
                "csv_filename": original.csv_filename,
                "file_name": original.file_name,
                "use_captcha": original.use_captcha,
                "proxy": original.proxy,
                "status": "DRAFT",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.commit()
        return {
            "success": True,
            "id": new_campaign_id,
            "name": new_name,
            "message": "Campaign duplicated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to duplicate campaign: {str(e)}"
        )


@router.get("/{campaign_id}/status")
@log_function("get_campaign_status")
def get_campaign_status(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get real-time campaign status"""
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    try:
        status_query = text(
            """SELECT status, total_urls, processed, successful, failed,
                      CASE WHEN total_urls > 0 
                           THEN ROUND((processed * 100.0 / total_urls), 2) 
                           ELSE 0 END as progress_percent,
                      CASE WHEN status IN ('COMPLETED', 'STOPPED', 'FAILED') 
                           THEN true ELSE false END as is_complete
               FROM campaigns 
               WHERE id = :campaign_id AND user_id = :user_id"""
        )

        result = db.execute(
            status_query, {"campaign_id": str(campaign_id), "user_id": str(user.id)}
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return {
            "campaign_id": str(campaign_id),
            "status": result.status,
            "total": result.total_urls or 0,
            "processed": result.processed or 0,
            "successful": result.successful or 0,
            "failed": result.failed or 0,
            "progress_percent": float(result.progress_percent or 0),
            "is_complete": result.is_complete,
            "message": (
                "Campaign processing completed"
                if result.is_complete
                else "Campaign in progress"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get campaign status: {str(e)}"
        )


# ===========================
# CAMPAIGN CRUD OPERATIONS
# ===========================


@router.get("")
@log_function("list_campaigns")
def list_campaigns(
    request: Request,  # Required Request parameter
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status_filter"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List campaigns with filtering and pagination"""
    # Set context variables for structured logging
    user_id_var.set(str(user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(user.id))

    client_ip = get_client_ip(request)

    # Use limit if provided, otherwise use per_page
    effective_limit = limit if limit is not None else per_page

    # Use either status_filter or status parameter
    status_value = status_filter or status

    logger.info(
        "Campaign list request started",
        context={
            "user_id": str(user.id),
            "client_ip": client_ip,
            "page": page,
            "per_page": per_page,
            "effective_limit": effective_limit,
            "status_filter": status_value,
        },
    )

    try:
        query_start = time.time()

        # Build base query
        base_query = """
            SELECT 
                id, user_id, name, status, csv_filename, file_name,
                total_urls, total_websites, processed, successful, failed,
                submitted_count, failed_count, email_fallback, no_form,
                message, proxy, use_captcha, error_message,
                created_at, updated_at, started_at, completed_at
            FROM campaigns 
            WHERE user_id = :user_id
        """

        params = {"user_id": str(user.id)}

        # Add status filter if provided
        if status_value:
            # Handle different status formats
            status_conditions = []
            status_upper = status_value.upper()

            if status_upper in ["ACTIVE", "RUNNING"]:
                status_conditions = [
                    "status IN ('ACTIVE', 'running', 'PROCESSING', 'RUNNING')"
                ]
            elif status_upper in ["COMPLETED"]:
                status_conditions = ["status IN ('COMPLETED', 'completed')"]
            elif status_upper in ["FAILED"]:
                status_conditions = ["status IN ('FAILED', 'failed')"]
            elif status_upper in ["DRAFT"]:
                status_conditions = ["status IN ('DRAFT', 'draft')"]
            else:
                status_conditions = ["status = :status_value"]
                params["status_value"] = status_value

            if status_conditions:
                base_query += f" AND ({' OR '.join(status_conditions)})"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({base_query}) as count_query"
        total = db.execute(text(count_query), params).scalar() or 0

        # Add ordering and pagination
        paginated_query = (
            f"{base_query} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )
        offset = (page - 1) * effective_limit
        params.update({"limit": effective_limit, "offset": offset})

        # Execute query
        result = db.execute(text(paginated_query), params).mappings().all()
        query_time = (time.time() - query_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="campaigns",
            duration_ms=query_time,
            affected_rows=len(result),
            success=True,
        )

        # Convert to response format
        campaigns = []
        for row in result:
            # Calculate additional metrics
            total_submissions = int(row.get("total_urls", 0) or 0)
            successful_submissions = int(row.get("successful", 0) or 0)
            failed_submissions = int(row.get("failed", 0) or 0)
            processed_submissions = int(row.get("processed", 0) or 0)

            progress_percent = 0
            if total_submissions > 0:
                progress_percent = round(
                    (processed_submissions / total_submissions) * 100, 2
                )

            success_rate = 0
            if processed_submissions > 0:
                success_rate = round(
                    (successful_submissions / processed_submissions) * 100, 2
                )

            campaign_dict = {
                "id": str(row["id"]),
                "user_id": str(row["user_id"]) if row["user_id"] else None,
                "name": row.get("name", "Untitled Campaign"),
                "status": row.get("status", "draft"),
                "csv_filename": row.get("csv_filename"),
                "file_name": row.get("file_name"),
                "total_urls": total_submissions,
                "total_websites": int(row.get("total_websites", 0) or 0),
                "processed": processed_submissions,
                "successful": successful_submissions,
                "failed": failed_submissions,
                "submitted_count": int(row.get("submitted_count", 0) or 0),
                "failed_count": int(row.get("failed_count", 0) or 0),
                "email_fallback": int(row.get("email_fallback", 0) or 0),
                "no_form": int(row.get("no_form", 0) or 0),
                "progress_percent": progress_percent,
                "success_rate": success_rate,
                "message": row.get("message"),
                "proxy": row.get("proxy"),
                "use_captcha": row.get("use_captcha"),
                "error_message": row.get("error_message"),
                "created_at": (
                    row["created_at"].isoformat() if row.get("created_at") else None
                ),
                "updated_at": (
                    row["updated_at"].isoformat() if row.get("updated_at") else None
                ),
                "started_at": (
                    row["started_at"].isoformat() if row.get("started_at") else None
                ),
                "completed_at": (
                    row["completed_at"].isoformat() if row.get("completed_at") else None
                ),
            }
            campaigns.append(campaign_dict)

        logger.info(
            "Campaigns retrieved successfully",
            context={
                "user_id": str(user.id),
                "campaigns_found": len(campaigns),
                "total_campaigns": total,
                "query_duration_ms": query_time,
                "page": page,
                "filtered": bool(status_value),
            },
        )

        # Track metrics
        app_logger.track_metric(
            name="campaigns_query_performance",
            value=query_time,
            properties={
                "result_count": len(campaigns),
                "total_count": total,
                "has_status_filter": bool(status_value),
                "user_id": str(user.id),
            },
        )

        # Track business event
        app_logger.track_business_event(
            event_name="campaigns_listed",
            properties={
                "user_id": str(user.id),
                "campaigns_returned": len(campaigns),
                "total_available": total,
                "filtered_by_status": status_value,
                "page": page,
                "per_page": effective_limit,
            },
            metrics={
                "query_time_ms": query_time,
                "avg_success_rate": (
                    sum(c.get("success_rate", 0) for c in campaigns) / len(campaigns)
                    if campaigns
                    else 0
                ),
            },
        )

        return campaigns

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Database error listing campaigns",
            context={
                "user_id": str(user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")
    except Exception as e:
        db.rollback()
        logger.error(
            "Unexpected error listing campaigns",
            context={
                "user_id": str(user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{campaign_id}")
@log_function("get_campaign")
def get_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single campaign by ID"""
    # Set context variables for structured logging
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(user.id), campaign_id=str(campaign_id))

    client_ip = get_client_ip(request)

    logger.info(
        "Campaign details request started",
        context={
            "user_id": str(user.id),
            "campaign_id": str(campaign_id),
            "client_ip": client_ip,
        },
    )

    try:
        query_start = time.time()

        # Query single campaign
        query = text(
            """
            SELECT 
                id, user_id, name, status, csv_filename, file_name,
                total_urls, total_websites, processed, successful, failed,
                submitted_count, failed_count, email_fallback, no_form,
                message, proxy, use_captcha, error_message,
                created_at, updated_at, started_at, completed_at
            FROM campaigns 
            WHERE id = :campaign_id AND user_id = :user_id
        """
        )

        result = (
            db.execute(
                query, {"campaign_id": str(campaign_id), "user_id": str(user.id)}
            )
            .mappings()
            .first()
        )

        query_time = (time.time() - query_start) * 1000

        logger.database_operation(
            operation="SELECT",
            table="campaigns",
            duration_ms=query_time,
            affected_rows=1 if result else 0,
            success=True,
        )

        if not result:
            logger.warning(
                "Campaign not found",
                context={"user_id": str(user.id), "campaign_id": str(campaign_id)},
            )
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Convert to response format (same logic as list_campaigns)
        row = result
        total_submissions = int(row.get("total_urls", 0) or 0)
        successful_submissions = int(row.get("successful", 0) or 0)
        failed_submissions = int(row.get("failed", 0) or 0)
        processed_submissions = int(row.get("processed", 0) or 0)

        progress_percent = 0
        if total_submissions > 0:
            progress_percent = round(
                (processed_submissions / total_submissions) * 100, 2
            )

        success_rate = 0
        if processed_submissions > 0:
            success_rate = round(
                (successful_submissions / processed_submissions) * 100, 2
            )

        campaign = {
            "id": str(row["id"]),
            "user_id": str(row["user_id"]) if row["user_id"] else None,
            "name": row.get("name", "Untitled Campaign"),
            "status": row.get("status", "draft"),
            "csv_filename": row.get("csv_filename"),
            "file_name": row.get("file_name"),
            "total_urls": total_submissions,
            "total_websites": int(row.get("total_websites", 0) or 0),
            "processed": processed_submissions,
            "successful": successful_submissions,
            "failed": failed_submissions,
            "submitted_count": int(row.get("submitted_count", 0) or 0),
            "failed_count": int(row.get("failed_count", 0) or 0),
            "email_fallback": int(row.get("email_fallback", 0) or 0),
            "no_form": int(row.get("no_form", 0) or 0),
            "progress_percent": progress_percent,
            "success_rate": success_rate,
            "message": row.get("message"),
            "proxy": row.get("proxy"),
            "use_captcha": row.get("use_captcha"),
            "error_message": row.get("error_message"),
            "created_at": (
                row["created_at"].isoformat() if row.get("created_at") else None
            ),
            "updated_at": (
                row["updated_at"].isoformat() if row.get("updated_at") else None
            ),
            "started_at": (
                row["started_at"].isoformat() if row.get("started_at") else None
            ),
            "completed_at": (
                row["completed_at"].isoformat() if row.get("completed_at") else None
            ),
        }

        logger.info(
            "Campaign details retrieved successfully",
            context={
                "user_id": str(user.id),
                "campaign_id": str(campaign_id),
                "campaign_name": campaign["name"],
                "status": campaign["status"],
                "query_duration_ms": query_time,
            },
        )

        # Track business event
        app_logger.track_user_action(
            action="view_campaign",
            target="campaign",
            properties={
                "campaign_id": str(campaign_id),
                "campaign_name": campaign["name"],
                "status": campaign["status"],
                "progress_percent": progress_percent,
                "success_rate": success_rate,
            },
        )

        return campaign

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Error retrieving campaign",
            context={
                "user_id": str(user.id),
                "campaign_id": str(campaign_id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch campaign: {str(e)}"
        )


@router.post("", response_model=None)
@log_function("create_campaign")
def create_campaign(
    request: Request,  # Required Request parameter
    name: str,
    message: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new campaign"""
    # Set context variables for structured logging
    user_id_var.set(str(user.id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(user.id))

    client_ip = get_client_ip(request)
    campaign_id = str(uuid.uuid4())
    campaign_id_var.set(campaign_id)

    logger.info(
        "Campaign creation started",
        context={
            "user_id": str(user.id),
            "campaign_id": campaign_id,
            "client_ip": client_ip,
            "campaign_name": name,
            "has_message": bool(message),
        },
    )

    try:
        # Validate input
        if not name or not name.strip():
            logger.warning(
                "Campaign creation failed - no name provided",
                context={"user_id": str(user.id)},
            )
            raise HTTPException(status_code=400, detail="Campaign name is required")

        campaign_name = name.strip()
        if len(campaign_name) > 255:
            logger.warning(
                "Campaign creation failed - name too long",
                context={"user_id": str(user.id), "name_length": len(campaign_name)},
            )
            raise HTTPException(
                status_code=400, detail="Campaign name too long (max 255 characters)"
            )

        # Create campaign
        create_start = time.time()
        now = datetime.utcnow()

        insert_query = text(
            """
            INSERT INTO campaigns (
                id, user_id, name, message, status, 
                created_at, updated_at
            ) VALUES (
                :id, :user_id, :name, :message, :status,
                :created_at, :updated_at
            )
        """
        )

        db.execute(
            insert_query,
            {
                "id": campaign_id,
                "user_id": str(user.id),
                "name": campaign_name,
                "message": message.strip() if message else None,
                "status": "DRAFT",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.commit()
        create_time = (time.time() - create_start) * 1000

        logger.database_operation(
            operation="INSERT",
            table="campaigns",
            duration_ms=create_time,
            affected_rows=1,
            success=True,
        )

        logger.info(
            "Campaign created successfully",
            context={
                "user_id": str(user.id),
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "create_duration_ms": create_time,
            },
        )

        # Track business events
        app_logger.track_business_event(
            event_name="campaign_created",
            properties={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "has_message": bool(message),
                "user_id": str(user.id),
            },
            metrics={"create_time_ms": create_time},
        )

        # Track user action
        app_logger.track_user_action(
            action="create_campaign",
            target="campaign",
            properties={"campaign_id": campaign_id, "campaign_name": campaign_name},
        )

        return {
            "id": campaign_id,
            "user_id": str(user.id),
            "name": campaign_name,
            "message": message,
            "status": "DRAFT",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Error creating campaign",
            context={
                "user_id": str(user.id),
                "campaign_id": campaign_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to create campaign: {str(e)}"
        )


@router.put("/{campaign_id}", response_model=None)
@log_function("update_campaign")
def update_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    name: Optional[str] = None,
    message: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a campaign"""
    # Set context variables for structured logging
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(user.id), campaign_id=str(campaign_id))

    client_ip = get_client_ip(request)

    # Track what's being updated
    update_fields = []
    if name is not None:
        update_fields.append("name")
    if message is not None:
        update_fields.append("message")
    if status is not None:
        update_fields.append("status")

    logger.info(
        "Campaign update started",
        context={
            "user_id": str(user.id),
            "campaign_id": str(campaign_id),
            "client_ip": client_ip,
            "update_fields": update_fields,
        },
    )

    try:
        update_start = time.time()

        # Check if campaign exists and belongs to user
        check_query = text(
            """
            SELECT name, status FROM campaigns 
            WHERE id = :campaign_id AND user_id = :user_id
        """
        )

        existing = (
            db.execute(
                check_query, {"campaign_id": str(campaign_id), "user_id": str(user.id)}
            )
            .mappings()
            .first()
        )

        if not existing:
            logger.warning(
                "Campaign not found for update",
                context={"user_id": str(user.id), "campaign_id": str(campaign_id)},
            )
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Build update query
        update_parts = []
        params = {"campaign_id": str(campaign_id), "user_id": str(user.id)}

        if name is not None:
            if not name.strip():
                raise HTTPException(
                    status_code=400, detail="Campaign name cannot be empty"
                )
            if len(name.strip()) > 255:
                raise HTTPException(status_code=400, detail="Campaign name too long")
            update_parts.append("name = :name")
            params["name"] = name.strip()

        if message is not None:
            update_parts.append("message = :message")
            params["message"] = message.strip() if message else None

        if status is not None:
            valid_statuses = ["DRAFT", "ACTIVE", "COMPLETED", "FAILED", "PAUSED"]
            if status.upper() not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {valid_statuses}",
                )
            update_parts.append("status = :status")
            params["status"] = status.upper()

        if update_parts:
            update_parts.append("updated_at = :updated_at")
            params["updated_at"] = datetime.utcnow()

            update_query = text(
                f"""
                UPDATE campaigns 
                SET {', '.join(update_parts)}
                WHERE id = :campaign_id AND user_id = :user_id
            """
            )

            db.execute(update_query, params)
            db.commit()

        update_time = (time.time() - update_start) * 1000

        logger.database_operation(
            operation="UPDATE",
            table="campaigns",
            duration_ms=update_time,
            affected_rows=1,
            success=True,
        )

        logger.info(
            "Campaign updated successfully",
            context={
                "user_id": str(user.id),
                "campaign_id": str(campaign_id),
                "fields_updated": update_fields,
                "update_duration_ms": update_time,
            },
        )

        # Track business event
        app_logger.track_business_event(
            event_name="campaign_updated",
            properties={
                "campaign_id": str(campaign_id),
                "fields_updated": update_fields,
                "user_id": str(user.id),
                "previous_name": existing["name"],
                "previous_status": existing["status"],
            },
            metrics={"update_time_ms": update_time},
        )

        return {
            "success": True,
            "message": "Campaign updated successfully",
            "fields_updated": update_fields,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Error updating campaign",
            context={
                "user_id": str(user.id),
                "campaign_id": str(campaign_id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to update campaign: {str(e)}"
        )


@router.delete("/{campaign_id}")
@log_function("delete_campaign")
def delete_campaign(
    request: Request,  # Required Request parameter
    campaign_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a campaign"""
    # Set context variables for structured logging
    user_id_var.set(str(user.id))
    campaign_id_var.set(str(campaign_id))

    app_logger = ApplicationInsightsLogger(db)
    app_logger.set_context(user_id=str(user.id), campaign_id=str(campaign_id))

    client_ip = get_client_ip(request)

    logger.info(
        "Campaign deletion started",
        context={
            "user_id": str(user.id),
            "campaign_id": str(campaign_id),
            "client_ip": client_ip,
        },
    )

    try:
        delete_start = time.time()

        # Check if campaign exists and belongs to user
        check_query = text(
            """
            SELECT name, status FROM campaigns 
            WHERE id = :campaign_id AND user_id = :user_id
        """
        )

        result = (
            db.execute(
                check_query, {"campaign_id": str(campaign_id), "user_id": str(user.id)}
            )
            .mappings()
            .first()
        )

        if not result:
            logger.warning(
                "Campaign not found for deletion",
                context={"user_id": str(user.id), "campaign_id": str(campaign_id)},
            )
            raise HTTPException(status_code=404, detail="Campaign not found")

        campaign_name = result["name"]
        campaign_status = result["status"]

        # Check if campaign can be deleted
        if campaign_status in ["ACTIVE", "running", "PROCESSING"]:
            logger.warning(
                "Cannot delete running campaign",
                context={
                    "user_id": str(user.id),
                    "campaign_id": str(campaign_id),
                    "status": campaign_status,
                },
            )
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a running campaign. Please stop it first.",
            )

        # Delete related submissions first
        delete_submissions = text(
            "DELETE FROM submissions WHERE campaign_id = :campaign_id"
        )
        submissions_deleted = db.execute(
            delete_submissions, {"campaign_id": str(campaign_id)}
        ).rowcount

        # Delete the campaign
        delete_campaign_query = text("DELETE FROM campaigns WHERE id = :campaign_id")
        db.execute(delete_campaign_query, {"campaign_id": str(campaign_id)})

        db.commit()
        delete_time = (time.time() - delete_start) * 1000

        logger.database_operation(
            operation="DELETE",
            table="campaigns",
            duration_ms=delete_time,
            affected_rows=1,
            success=True,
        )

        logger.info(
            "Campaign deleted successfully",
            context={
                "user_id": str(user.id),
                "campaign_id": str(campaign_id),
                "campaign_name": campaign_name,
                "submissions_deleted": submissions_deleted,
                "delete_duration_ms": delete_time,
            },
        )

        # Track business events
        app_logger.track_business_event(
            event_name="campaign_deleted",
            properties={
                "campaign_id": str(campaign_id),
                "campaign_name": campaign_name,
                "submissions_deleted": submissions_deleted,
                "user_id": str(user.id),
            },
            metrics={"delete_time_ms": delete_time},
        )

        # Track security event for deletion
        app_logger.track_security_event(
            event_name="resource_deleted",
            user_id=str(user.id),
            resource_type="campaign",
            resource_id=str(campaign_id),
            ip_address=client_ip,
            success=True,
        )

        return {
            "success": True,
            "message": f"Campaign '{campaign_name}' and {submissions_deleted} related submissions deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Error deleting campaign",
            context={
                "user_id": str(user.id),
                "campaign_id": str(campaign_id),
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        app_logger.track_exception(e, handled=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete campaign: {str(e)}"
        )
