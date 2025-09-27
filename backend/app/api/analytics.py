# app/api/analytics.py - Complete Fixed Version
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

# Enhanced logging imports
from app.logging import get_logger, log_function, log_exceptions, log_performance
from app.logging.core import user_id_var, request_id_var

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Initialize logger
logger = get_logger(__name__)


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request headers"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


@router.get("/debug")
async def debug_analytics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check database connection and data"""
    try:
        # Test basic connection
        db_test = db.execute(text("SELECT NOW(), version()")).fetchone()

        # Check if user exists and get basic info
        user_check = db.execute(
            text("SELECT id, email, role FROM users WHERE id = :uid"),
            {"uid": str(current_user.id)},
        ).fetchone()

        # Check campaigns for this user
        campaigns_check = db.execute(
            text(
                "SELECT COUNT(*) as count, status FROM campaigns WHERE user_id = :uid GROUP BY status"
            ),
            {"uid": str(current_user.id)},
        ).fetchall()

        # Check submissions for this user
        submissions_check = db.execute(
            text(
                "SELECT COUNT(*) as count, success FROM submissions WHERE user_id = :uid GROUP BY success"
            ),
            {"uid": str(current_user.id)},
        ).fetchall()

        # Check all campaigns in system (to see if user_id mismatch)
        all_campaigns = db.execute(
            text("SELECT DISTINCT user_id FROM campaigns LIMIT 10")
        ).fetchall()

        # Check all users in system
        all_users = db.execute(text("SELECT id, email FROM users LIMIT 10")).fetchall()

        return {
            "database_connection": "OK",
            "database_time": str(db_test[0]) if db_test else None,
            "database_version": str(db_test[1]) if db_test else None,
            "current_user": (
                {
                    "id": str(user_check[0]) if user_check else None,
                    "email": str(user_check[1]) if user_check else None,
                    "role": str(user_check[2]) if user_check else None,
                }
                if user_check
                else None
            ),
            "campaigns_by_status": [
                {"status": row[1], "count": row[0]} for row in campaigns_check
            ],
            "submissions_by_success": [
                {"success": row[1], "count": row[0]} for row in submissions_check
            ],
            "all_campaign_user_ids": [str(row[0]) for row in all_campaigns],
            "all_users": [
                {"id": str(row[0]), "email": str(row[1])} for row in all_users
            ],
        }

    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {"error": str(e), "database_connection": "FAILED"}


@router.get("/user")
@log_function("get_user_analytics")
async def analytics_user(
    # Query parameters first
    include_detailed: bool = Query(False, description="Include detailed breakdowns"),
    days: Optional[int] = Query(None, description="Filter by number of days"),
    # Dependencies next
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Request object last
    request: Request = None,
):
    """Get comprehensive user analytics summary"""
    user_id_var.set(str(current_user.id))
    client_ip = get_client_ip(request) if request else "unknown"

    logger.info(
        "User analytics request",
        context={
            "user_id": str(current_user.id),
            "ip": client_ip,
            "include_detailed": include_detailed,
            "days_filter": days,
        },
    )

    try:
        total_start = time.time()

        # Test database connection first
        try:
            db.execute(text("SELECT 1")).fetchone()
            logger.info("Database connection verified")
        except Exception as db_error:
            logger.error(f"Database connection failed: {db_error}")
            raise HTTPException(status_code=503, detail="Database connection failed")

        # Build date filter based on days parameter
        date_filter = ""
        if days:
            if days == 1:
                date_filter = " AND DATE(created_at) = CURRENT_DATE"
            else:
                date_filter = (
                    f" AND created_at >= CURRENT_DATE - INTERVAL '{days} days'"
                )

        # Get campaign stats with better error handling
        campaigns_query = text(
            f"""
            SELECT 
                COUNT(*)::int as total_campaigns,
                COUNT(CASE WHEN status IN ('ACTIVE', 'running', 'PROCESSING') THEN 1 END)::int as active_campaigns,
                COUNT(CASE WHEN status IN ('COMPLETED', 'completed') THEN 1 END)::int as completed_campaigns,
                COALESCE(SUM(total_urls), 0)::int as total_urls,
                COALESCE(SUM(submitted_count), 0)::int as submitted_count,
                COALESCE(SUM(successful), 0)::int as successful,
                COALESCE(SUM(failed), 0)::int as failed,
                COALESCE(SUM(processed), 0)::int as processed
            FROM campaigns 
            WHERE user_id = :uid{date_filter}
        """
        )

        try:
            campaign_result = db.execute(campaigns_query, {"uid": str(current_user.id)})
            campaign_stats = campaign_result.mappings().first()
            logger.info(
                f"Campaign query result: {dict(campaign_stats) if campaign_stats else None}"
            )
        except Exception as e:
            logger.error(f"Campaign query failed: {e}")
            campaign_stats = None

        # Get submission stats with better error handling
        submissions_query = text(
            f"""
            SELECT 
                COUNT(*)::int as total_submissions,
                COUNT(CASE WHEN success = true THEN 1 END)::int as successful_submissions,
                COUNT(CASE WHEN success = false THEN 1 END)::int as failed_submissions,
                COUNT(CASE WHEN status = 'pending' THEN 1 END)::int as pending_submissions,
                COUNT(CASE WHEN captcha_encountered = true THEN 1 END)::int as captcha_submissions,
                COUNT(CASE WHEN captcha_solved = true THEN 1 END)::int as captcha_solved,
                COALESCE(AVG(retry_count), 0)::float as avg_retry_count,
                COUNT(CASE WHEN email_extracted IS NOT NULL THEN 1 END)::int as emails_extracted
            FROM submissions 
            WHERE user_id = :uid{date_filter}
        """
        )

        try:
            submission_result = db.execute(
                submissions_query, {"uid": str(current_user.id)}
            )
            submission_stats = submission_result.mappings().first()
            logger.info(
                f"Submission query result: {dict(submission_stats) if submission_stats else None}"
            )
        except Exception as e:
            logger.error(f"Submission query failed: {e}")
            submission_stats = None

        # Website count
        try:
            websites_result = db.execute(
                text(
                    "SELECT COUNT(*)::int as websites_count FROM websites WHERE user_id = :uid"
                ),
                {"uid": str(current_user.id)},
            )
            website_stats = websites_result.mappings().first()
            logger.info(
                f"Website query result: {dict(website_stats) if website_stats else None}"
            )
        except Exception as e:
            logger.error(f"Website query failed: {e}")
            website_stats = None

        # Process results with null safety
        campaign_stats = campaign_stats or {}
        submission_stats = submission_stats or {}
        website_stats = website_stats or {}

        total_campaigns = int(campaign_stats.get("total_campaigns", 0) or 0)
        active_campaigns = int(campaign_stats.get("active_campaigns", 0) or 0)
        total_submissions = int(submission_stats.get("total_submissions", 0) or 0)
        successful_submissions = int(
            submission_stats.get("successful_submissions", 0) or 0
        )
        failed_submissions = int(submission_stats.get("failed_submissions", 0) or 0)

        # Calculate rates
        success_rate = (
            (successful_submissions / total_submissions * 100)
            if total_submissions > 0
            else 0
        )

        captcha_encounter_rate = (
            (
                int(submission_stats.get("captcha_submissions", 0) or 0)
                / total_submissions
                * 100
            )
            if total_submissions > 0
            else 0
        )

        captcha_success_rate = 0
        captcha_total = int(submission_stats.get("captcha_submissions", 0) or 0)
        if captcha_total > 0:
            captcha_success_rate = (
                int(submission_stats.get("captcha_solved", 0) or 0)
                / captcha_total
                * 100
            )

        # Get recent activity if detailed view requested
        recent_activity = {}
        if include_detailed:
            try:
                recent_date_filter = (
                    date_filter
                    if days and days <= 7
                    else " AND created_at >= NOW() - INTERVAL '7 days'"
                )
                recent_query = text(
                    f"""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        MAX(created_at) as last_activity
                    FROM submissions 
                    WHERE user_id = :uid{recent_date_filter}
                    GROUP BY status
                    ORDER BY count DESC
                """
                )
                recent_results = (
                    db.execute(recent_query, {"uid": str(current_user.id)})
                    .mappings()
                    .all()
                )

                recent_activity = {
                    "recent_submissions_by_status": [
                        {
                            "status": row["status"],
                            "count": int(row["count"]),
                            "last_activity": (
                                row["last_activity"].isoformat()
                                if row["last_activity"]
                                else None
                            ),
                        }
                        for row in recent_results
                    ]
                }
            except Exception as e:
                logger.warning(
                    "Failed to fetch recent activity",
                    context={"user_id": str(current_user.id), "error": str(e)},
                )
                recent_activity = {"recent_submissions_by_status": []}

        # Always return a complete response structure
        payload = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "campaigns_count": total_campaigns,
            "websites_count": int(website_stats.get("websites_count", 0) or 0),
            "active_campaigns": active_campaigns,
            "total_submissions": total_submissions,
            "successful_submissions": successful_submissions,
            "failed_submissions": failed_submissions,
            "captcha_submissions": int(
                submission_stats.get("captcha_submissions", 0) or 0
            ),
            "captcha_solved": int(submission_stats.get("captcha_solved", 0) or 0),
            "emails_extracted": int(submission_stats.get("emails_extracted", 0) or 0),
            "avg_retry_count": round(
                float(submission_stats.get("avg_retry_count", 0) or 0), 2
            ),
            "unique_campaigns_used": total_campaigns,
            "success_rate": round(success_rate, 2),
            "captcha_encounter_rate": round(captcha_encounter_rate, 2),
            "captcha_success_rate": round(captcha_success_rate, 2),
        }

        if include_detailed:
            payload["recent_activity"] = recent_activity

        total_time = (time.time() - total_start) * 1000

        logger.info(
            f"Analytics payload prepared",
            context={
                "user_id": str(current_user.id),
                "payload_size": len(str(payload)),
                "query_time_ms": total_time,
                "has_campaigns": total_campaigns > 0,
                "has_submissions": total_submissions > 0,
            },
        )

        return payload

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={"endpoint": "/analytics/user", "user_id": str(current_user.id)},
        )

        # Return a proper error response instead of empty data
        error_response = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "campaigns_count": 0,
            "websites_count": 0,
            "total_submissions": 0,
            "successful_submissions": 0,
            "failed_submissions": 0,
            "success_rate": 0,
            "captcha_encounter_rate": 0,
            "captcha_success_rate": 0,
            "error": True,
            "error_message": f"Analytics temporarily unavailable: {str(e)[:100]}",
        }

        logger.error(f"Returning error response: {error_response}")
        return error_response


@router.get("/daily-stats")
@log_function("get_daily_analytics_stats")
async def analytics_daily_stats(
    # Query parameters first
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    campaign_id: Optional[str] = Query(None, description="Filter by specific campaign"),
    include_trends: bool = Query(False, description="Include trend analysis"),
    # Dependencies next
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Request object last
    request: Request = None,
):
    """Get daily submission statistics with trend analysis"""
    user_id_var.set(str(current_user.id))
    client_ip = get_client_ip(request) if request else "unknown"

    logger.info(
        "Daily analytics stats request",
        context={
            "user_id": str(current_user.id),
            "ip": client_ip,
            "days": days,
            "campaign_id": campaign_id,
            "include_trends": include_trends,
        },
    )

    try:
        stats_start = time.time()

        params = {"uid": str(current_user.id)}

        if days == 1:
            where_clause = "s.user_id = :uid AND DATE(s.created_at) = CURRENT_DATE"
        elif days == 7:
            where_clause = (
                "s.user_id = :uid AND s.created_at >= CURRENT_DATE - INTERVAL '7 days'"
            )
        elif days == 30:
            where_clause = (
                "s.user_id = :uid AND s.created_at >= CURRENT_DATE - INTERVAL '30 days'"
            )
        else:
            where_clause = f"s.user_id = :uid AND s.created_at >= CURRENT_DATE - INTERVAL '{days} days'"

        if campaign_id:
            where_clause += " AND s.campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id

        daily_query = text(
            f"""
            SELECT
                CAST(date_trunc('day', s.created_at) AS date) AS day,
                COUNT(*)::int AS total,
                SUM(CASE WHEN s.success = true THEN 1 ELSE 0 END)::int AS success,
                SUM(CASE WHEN s.success = false THEN 1 ELSE 0 END)::int AS failed,
                SUM(CASE WHEN s.captcha_encountered = true THEN 1 ELSE 0 END)::int AS captcha_encountered,
                SUM(CASE WHEN s.captcha_solved = true THEN 1 ELSE 0 END)::int AS captcha_solved,
                COALESCE(AVG(s.retry_count), 0)::numeric(10,2) AS avg_retries
            FROM submissions s
            WHERE {where_clause}
            GROUP BY 1
            ORDER BY 1 ASC
        """
        )

        try:
            rows = db.execute(daily_query, params).mappings().all()
        except Exception as e:
            logger.error(f"Daily stats query failed: {e}")
            rows = []

        data = []
        for r in rows:
            day_data = {
                "day": (
                    r["day"].isoformat()
                    if hasattr(r["day"], "isoformat")
                    else str(r["day"])
                ),
                "total": int(r.get("total", 0) or 0),
                "success": int(r.get("success", 0) or 0),
                "failed": int(r.get("failed", 0) or 0),
                "captcha_encountered": int(r.get("captcha_encountered", 0) or 0),
                "captcha_solved": int(r.get("captcha_solved", 0) or 0),
                "avg_retries": float(r.get("avg_retries", 0) or 0),
                "success_rate": 0,
            }

            if day_data["total"] > 0:
                day_data["success_rate"] = round(
                    (day_data["success"] / day_data["total"]) * 100, 2
                )

            data.append(day_data)

        # Add empty day for single day query with no data
        if days == 1 and len(data) == 0:
            data = [
                {
                    "day": datetime.now().date().isoformat(),
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "captcha_encountered": 0,
                    "captcha_solved": 0,
                    "avg_retries": 0,
                    "success_rate": 0,
                }
            ]

        total_submissions = sum(d["total"] for d in data)
        total_success = sum(d["success"] for d in data)
        overall_success_rate = (
            (total_success / total_submissions * 100) if total_submissions > 0 else 0
        )

        stats_time = (time.time() - stats_start) * 1000

        logger.info(
            f"Daily analytics stats retrieved",
            context={
                "user_id": str(current_user.id),
                "days": days,
                "campaign_id": campaign_id,
                "data_points": len(data),
                "total_submissions": total_submissions,
                "query_time_ms": stats_time,
            },
        )

        response = {
            "days": int(days),
            "campaign_filter": campaign_id,
            "series": data,
            "summary": {
                "total_submissions": total_submissions,
                "total_success": total_success,
                "total_failed": sum(d["failed"] for d in data),
                "overall_success_rate": round(overall_success_rate, 2),
                "avg_daily_submissions": round(
                    total_submissions / max(len(data), 1), 2
                ),
                "active_days": len([d for d in data if d["total"] > 0]),
                "data_points": len(data),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        return response

    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={
                "endpoint": "/analytics/daily-stats",
                "user_id": str(current_user.id),
                "days": days,
                "campaign_id": campaign_id,
            },
        )
        return {
            "days": int(days),
            "campaign_filter": campaign_id,
            "series": [],
            "summary": {
                "total_submissions": 0,
                "total_success": 0,
                "total_failed": 0,
                "overall_success_rate": 0,
                "avg_daily_submissions": 0,
                "active_days": 0,
                "data_points": 0,
            },
            "error": f"Daily statistics temporarily unavailable: {str(e)}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/performance")
@log_function("get_performance_analytics")
async def analytics_performance(
    # Query parameters first
    limit: int = Query(10, ge=1, le=50, description="Limit results per category"),
    time_range: int = Query(30, ge=1, le=365, description="Days to analyze"),
    # Dependencies next
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Request object last
    request: Request = None,
):
    """Get performance analytics for campaigns"""
    user_id_var.set(str(current_user.id))
    client_ip = get_client_ip(request) if request else "unknown"

    logger.info(
        "Performance analytics request",
        context={
            "user_id": str(current_user.id),
            "ip": client_ip,
            "limit": limit,
            "time_range": time_range,
        },
    )

    try:
        perf_start = time.time()

        campaign_query = text(
            """
            SELECT 
                c.id,
                c.name,
                c.status,
                COALESCE(c.total_urls, 0) as total_urls,
                COALESCE(c.total_websites, 0) as total_websites,
                COALESCE(c.processed, 0) as processed,
                COALESCE(c.successful, 0) as successful,
                COALESCE(c.failed, 0) as failed,
                CASE 
                    WHEN COALESCE(c.total_websites, 0) > 0 
                    THEN ROUND(CAST((COALESCE(c.processed, 0)::float / c.total_websites) * 100 AS numeric), 2)
                    ELSE 0 
                END as processing_rate,
                CASE 
                    WHEN COALESCE(c.processed, 0) > 0 
                    THEN ROUND(CAST((COALESCE(c.successful, 0)::float / c.processed) * 100 AS numeric), 2)
                    ELSE 0 
                END as success_rate,
                c.created_at,
                c.started_at,
                c.completed_at
            FROM campaigns c
            WHERE c.user_id = :uid
            AND c.created_at >= NOW() - make_interval(days => :time_range)
            ORDER BY c.created_at DESC
            LIMIT :limit
        """
        )

        try:
            campaigns = (
                db.execute(
                    campaign_query,
                    {
                        "uid": str(current_user.id),
                        "time_range": time_range,
                        "limit": limit,
                    },
                )
                .mappings()
                .all()
            )
        except Exception as e:
            logger.error(f"Performance query failed: {e}")
            campaigns = []

        summary_query = text(
            """
            SELECT
                COUNT(DISTINCT c.id) as total_campaigns,
                COUNT(DISTINCT CASE WHEN c.status IN ('running', 'ACTIVE', 'PROCESSING') THEN c.id END) as active_campaigns,
                COUNT(DISTINCT CASE WHEN c.status IN ('completed', 'COMPLETED') THEN c.id END) as completed_campaigns,
                ROUND(CAST(AVG(
                    CASE WHEN COALESCE(c.successful, 0) > 0 AND COALESCE(c.processed, 0) > 0 
                    THEN (COALESCE(c.successful, 0)::float / COALESCE(c.processed, 1)) * 100 
                    END
                ) AS numeric), 2) as avg_campaign_success_rate
            FROM campaigns c
            WHERE c.user_id = :uid
            AND c.created_at >= NOW() - make_interval(days => :time_range)
        """
        )

        try:
            summary_row = (
                db.execute(
                    summary_query,
                    {"uid": str(current_user.id), "time_range": time_range},
                )
                .mappings()
                .first()
                or {}
            )
        except Exception as e:
            logger.error(f"Performance summary query failed: {e}")
            summary_row = {}

        performance_data = {
            "time_range_days": time_range,
            "limit": limit,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "campaigns": [
                {
                    "id": str(c["id"]),
                    "name": c["name"] or "Untitled Campaign",
                    "status": c["status"] or "unknown",
                    "total_urls": int(c.get("total_urls", 0) or 0),
                    "total_websites": int(c.get("total_websites", 0) or 0),
                    "processed": int(c.get("processed", 0) or 0),
                    "successful": int(c.get("successful", 0) or 0),
                    "failed": int(c.get("failed", 0) or 0),
                    "processing_rate": float(c.get("processing_rate", 0) or 0),
                    "success_rate": float(c.get("success_rate", 0) or 0),
                    "created_at": (
                        c["created_at"].isoformat() if c["created_at"] else None
                    ),
                    "started_at": (
                        c["started_at"].isoformat() if c["started_at"] else None
                    ),
                    "completed_at": (
                        c["completed_at"].isoformat() if c["completed_at"] else None
                    ),
                }
                for c in campaigns
            ],
            "domain_statistics": [],
            "summary": {
                "total_campaigns": int(summary_row.get("total_campaigns", 0) or 0),
                "active_campaigns": int(summary_row.get("active_campaigns", 0) or 0),
                "completed_campaigns": int(
                    summary_row.get("completed_campaigns", 0) or 0
                ),
                "unique_domains": 0,
                "avg_campaign_success_rate": round(
                    float(summary_row.get("avg_campaign_success_rate", 0) or 0), 2
                ),
            },
        }

        perf_time = (time.time() - perf_start) * 1000

        logger.info(
            f"Performance analytics retrieved",
            context={
                "user_id": str(current_user.id),
                "campaigns_analyzed": len(campaigns),
                "time_range": time_range,
                "avg_success_rate": performance_data["summary"][
                    "avg_campaign_success_rate"
                ],
                "query_time_ms": perf_time,
            },
        )

        return performance_data

    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={
                "endpoint": "/analytics/performance",
                "user_id": str(current_user.id),
                "time_range": time_range,
                "limit": limit,
            },
        )
        return {
            "time_range_days": time_range,
            "limit": limit,
            "campaigns": [],
            "domain_statistics": [],
            "summary": {
                "total_campaigns": 0,
                "active_campaigns": 0,
                "completed_campaigns": 0,
                "unique_domains": 0,
                "avg_campaign_success_rate": 0,
            },
            "error": f"Performance analytics temporarily unavailable: {str(e)}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/revenue")
@log_function("get_revenue_analytics")
async def get_revenue_analytics(
    # Query parameters first
    days: Optional[int] = Query(None, description="Filter by number of days"),
    # Dependencies next
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Request object last
    request: Request = None,
):
    """Get revenue analytics based on successful submissions"""
    user_id_var.set(str(current_user.id))

    logger.info(
        "Revenue analytics request",
        context={
            "user_id": str(current_user.id),
            "days_filter": days,
            "ip": get_client_ip(request) if request else "unknown",
        },
    )

    try:
        revenue_start = time.time()
        price_per_submission = 0.50

        # Build date filter
        date_filter = ""
        if days:
            if days == 1:
                date_filter = " AND DATE(created_at) = CURRENT_DATE"
            else:
                date_filter = (
                    f" AND created_at >= CURRENT_DATE - INTERVAL '{days} days'"
                )

        # Get revenue stats for filtered period
        revenue_query = text(
            f"""
            SELECT 
                COUNT(CASE WHEN success = true THEN 1 END) as successful_submissions
            FROM submissions 
            WHERE user_id = :uid{date_filter}
        """
        )

        try:
            result = (
                db.execute(revenue_query, {"uid": str(current_user.id)})
                .mappings()
                .first()
            )
            successful_count = result["successful_submissions"] or 0
        except Exception as e:
            logger.error(f"Revenue query failed: {e}")
            successful_count = 0

        total_revenue = successful_count * price_per_submission

        # Calculate revenue change if we have comparison data
        revenue_change = "N/A"
        if days and days > 1:
            try:
                previous_query = text(
                    f"""
                    SELECT COUNT(CASE WHEN success = true THEN 1 END) as prev_success
                    FROM submissions 
                    WHERE user_id = :uid 
                    AND created_at >= CURRENT_DATE - INTERVAL '{days * 2} days'
                    AND created_at < CURRENT_DATE - INTERVAL '{days} days'
                """
                )
                prev_result = (
                    db.execute(previous_query, {"uid": str(current_user.id)})
                    .mappings()
                    .first()
                )
                prev_revenue = (prev_result["prev_success"] or 0) * price_per_submission

                if prev_revenue > 0:
                    change_percent = (
                        (total_revenue - prev_revenue) / prev_revenue
                    ) * 100
                    revenue_change = (
                        f"{'+' if change_percent > 0 else ''}{change_percent:.1f}%"
                    )
                elif total_revenue > 0:
                    revenue_change = "+100%"
            except Exception as e:
                logger.error(f"Revenue change calculation failed: {e}")

        revenue_time = (time.time() - revenue_start) * 1000

        logger.info(
            f"Revenue analytics calculated",
            context={
                "user_id": str(current_user.id),
                "days_filter": days,
                "successful_submissions": successful_count,
                "total_revenue": total_revenue,
                "revenue_change": revenue_change,
                "query_time_ms": revenue_time,
            },
        )

        return {
            "price_per_submission": price_per_submission,
            "total_revenue": total_revenue,
            "revenue_change": revenue_change,
            "success_rate_change": "N/A",
            "successful_submissions": successful_count,
        }

    except Exception as e:
        logger.exception(
            e,
            handled=True,
            context={
                "endpoint": "/analytics/revenue",
                "user_id": str(current_user.id),
                "days": days,
            },
        )
        return {
            "price_per_submission": 0.50,
            "total_revenue": 0,
            "revenue_change": "N/A",
            "error": str(e),
        }
