# app/api/dashboard.py - Dashboard overview endpoints
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    campaigns: Dict[str, Any]
    submissions: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


@router.get("/overview", response_model=DashboardStats)
def get_dashboard_overview(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard overview with key metrics"""
    try:
        user_id = str(current_user.id)

        # Campaign statistics
        campaigns_query = text(
            """
            SELECT 
                COUNT(*) as total_campaigns,
                COUNT(CASE WHEN status IN ('ACTIVE', 'PROCESSING') THEN 1 END) as active_campaigns,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_campaigns,
                COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_campaigns,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as campaigns_this_week,
                COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as campaigns_this_month
            FROM campaigns WHERE user_id = :user_id
        """
        )

        campaigns_result = (
            db.execute(campaigns_query, {"user_id": user_id}).mappings().first()
        )
        campaigns_stats = dict(campaigns_result) if campaigns_result else {}

        # Submission statistics
        submissions_query = text(
            """
            SELECT 
                COUNT(s.id) as total_submissions,
                COUNT(CASE WHEN s.success = true THEN 1 END) as successful_submissions,
                COUNT(CASE WHEN s.success = false THEN 1 END) as failed_submissions,
                COUNT(CASE WHEN s.status = 'pending' THEN 1 END) as pending_submissions,
                COUNT(CASE WHEN s.captcha_encountered = true THEN 1 END) as captcha_submissions,
                COUNT(CASE WHEN s.created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as submissions_today,
                COUNT(CASE WHEN s.created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as submissions_this_week
            FROM submissions s
            JOIN campaigns c ON s.campaign_id = c.id
            WHERE c.user_id = :user_id
        """
        )

        submissions_result = (
            db.execute(submissions_query, {"user_id": user_id}).mappings().first()
        )
        submissions_stats = dict(submissions_result) if submissions_result else {}

        # Calculate success rate
        total_subs = submissions_stats.get("total_submissions", 0)
        successful_subs = submissions_stats.get("successful_submissions", 0)
        success_rate = (successful_subs / total_subs * 100) if total_subs > 0 else 0

        # Recent activity
        recent_activity_query = text(
            """
            SELECT 
                'campaign' as type,
                c.name as title,
                c.status as status,
                c.created_at as timestamp,
                c.id as entity_id
            FROM campaigns c
            WHERE c.user_id = :user_id
            
            UNION ALL
            
            SELECT 
                'submission' as type,
                CONCAT('Submission to ', w.domain) as title,
                s.status as status,
                s.created_at as timestamp,
                s.id as entity_id
            FROM submissions s
            JOIN campaigns c ON s.campaign_id = c.id
            LEFT JOIN websites w ON s.website_id = w.id
            WHERE c.user_id = :user_id
            
            ORDER BY timestamp DESC
            LIMIT 10
        """
        )

        recent_activity_result = (
            db.execute(recent_activity_query, {"user_id": user_id}).mappings().all()
        )

        recent_activity = []
        for activity in recent_activity_result:
            activity_dict = dict(activity)
            if activity_dict["timestamp"]:
                activity_dict["timestamp"] = activity_dict["timestamp"].isoformat()
            recent_activity.append(activity_dict)

        # Performance metrics
        performance_metrics = {
            "success_rate": round(success_rate, 2),
            "avg_submissions_per_campaign": round(
                submissions_stats.get("total_submissions", 0)
                / max(campaigns_stats.get("total_campaigns", 1), 1),
                2,
            ),
            "captcha_encounter_rate": round(
                (submissions_stats.get("captcha_submissions", 0) / max(total_subs, 1))
                * 100,
                2,
            ),
            "active_campaign_ratio": round(
                (
                    campaigns_stats.get("active_campaigns", 0)
                    / max(campaigns_stats.get("total_campaigns", 1), 1)
                )
                * 100,
                2,
            ),
        }

        return DashboardStats(
            campaigns=campaigns_stats,
            submissions=submissions_stats,
            recent_activity=recent_activity,
            performance_metrics=performance_metrics,
        )

    except Exception as e:
        print(f"[DASHBOARD ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/quick-stats")
def get_quick_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get quick stats for the top navigation bar"""
    try:
        user_id = str(current_user.id)

        # Quick stats query
        stats_query = text(
            """
            SELECT 
                (SELECT COUNT(*) FROM campaigns WHERE user_id = :user_id AND status IN ('ACTIVE', 'PROCESSING')) as active_campaigns,
                (SELECT COUNT(*) FROM submissions s JOIN campaigns c ON s.campaign_id = c.id WHERE c.user_id = :user_id AND s.status = 'pending') as pending_submissions,
                (SELECT COUNT(*) FROM submissions s JOIN campaigns c ON s.campaign_id = c.id WHERE c.user_id = :user_id AND s.created_at >= NOW() - INTERVAL '24 hours') as todays_submissions
        """
        )

        result = db.execute(stats_query, {"user_id": user_id}).mappings().first()

        return (
            dict(result)
            if result
            else {
                "active_campaigns": 0,
                "pending_submissions": 0,
                "todays_submissions": 0,
            }
        )

    except Exception as e:
        print(f"[QUICK STATS ERROR] {e}")
        return {
            "active_campaigns": 0,
            "pending_submissions": 0,
            "todays_submissions": 0,
        }


@router.get("/recent-campaigns")
def get_recent_campaigns(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent campaigns for quick access"""
    try:
        user_id = str(current_user.id)

        campaigns_query = text(
            """
            SELECT 
                id, name, status, total_urls, successful, failed,
                created_at, updated_at
            FROM campaigns 
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
            LIMIT :limit
        """
        )

        result = (
            db.execute(campaigns_query, {"user_id": user_id, "limit": limit})
            .mappings()
            .all()
        )

        campaigns = []
        for campaign in result:
            campaign_dict = dict(campaign)
            # Convert dates to ISO strings
            for field in ["created_at", "updated_at"]:
                if campaign_dict.get(field):
                    campaign_dict[field] = campaign_dict[field].isoformat()
            campaigns.append(campaign_dict)

        return {"campaigns": campaigns}

    except Exception as e:
        print(f"[RECENT CAMPAIGNS ERROR] {e}")
        return {"campaigns": []}
