# app/services/analytics_service.py - FIXED VERSION

import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from fastapi import HTTPException

from app.models.user import User
from app.models.campaign import Campaign, CampaignStatus
from app.models.submission import Submission, SubmissionStatus  # Import enums
from app.models.website import Website
from app.schemas.analytics import (
    SubmissionStats,
    CampaignAnalytics,
    UserAnalytics,
    SystemAnalytics,
)


class AnalyticsService:
    """Service for generating analytics and reports with proper enum handling"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_analytics(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> UserAnalytics:
        """Get analytics for a specific user with error handling"""
        try:
            print(
                f"[ANALYTICS SERVICE] 📊 Getting analytics for user: {str(user_id)[:8]}..."
            )

            query = self.db.query(Campaign).filter(Campaign.user_id == user_id)

            if start_date:
                query = query.filter(Campaign.started_at >= start_date)
            if end_date:
                query = query.filter(Campaign.started_at <= end_date)

            total_campaigns = query.count()

            # Get submission stats for this user with proper enum handling
            submission_query = self.db.query(Submission).filter(
                Submission.user_id == user_id
            )

            if start_date:
                submission_query = submission_query.filter(
                    Submission.created_at >= start_date
                )
            if end_date:
                submission_query = submission_query.filter(
                    Submission.created_at <= end_date
                )

            total_submissions = submission_query.count()

            # FIXED: Use proper enum values instead of strings
            successful_submissions = submission_query.filter(
                Submission.status.in_(
                    [SubmissionStatus.SUCCESS, SubmissionStatus.COMPLETED]
                )
            ).count()

            failed_submissions = submission_query.filter(
                Submission.status == SubmissionStatus.FAILED
            ).count()

            pending_submissions = submission_query.filter(
                Submission.status == SubmissionStatus.PENDING
            ).count()

            success_rate = (
                (successful_submissions / total_submissions * 100)
                if total_submissions > 0
                else 0
            )

            stats = SubmissionStats(
                total_submissions=total_submissions,
                successful_submissions=successful_submissions,
                failed_submissions=failed_submissions,
                pending_submissions=pending_submissions,
                success_rate=round(success_rate, 2),
            )

            print(
                f"[ANALYTICS SERVICE] ✅ Analytics: {successful_submissions}/{total_submissions} successful"
            )

            return UserAnalytics(
                user_id=str(user_id),
                total_campaigns=total_campaigns,
                total_submissions=total_submissions,
                stats=stats,
            )

        except Exception as e:
            print(f"[ANALYTICS SERVICE] ❌ Failed to get user analytics: {str(e)}")
            # Return zero stats instead of failing
            stats = SubmissionStats(
                total_submissions=0,
                successful_submissions=0,
                failed_submissions=0,
                pending_submissions=0,
                success_rate=0,
            )
            return UserAnalytics(
                user_id=str(user_id),
                total_campaigns=0,
                total_submissions=0,
                stats=stats,
            )

    def get_campaign_analytics(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID
    ) -> CampaignAnalytics:
        """Get analytics for a specific campaign with error handling"""
        try:
            # Verify campaign belongs to user
            campaign = (
                self.db.query(Campaign)
                .filter(and_(Campaign.id == campaign_id, Campaign.user_id == user_id))
                .first()
            )

            if not campaign:
                raise HTTPException(status_code=404, detail="Campaign not found")

            # Get submission counts with proper enum handling
            submission_counts = (
                self.db.query(Submission.status, func.count(Submission.id))
                .filter(Submission.campaign_id == campaign_id)
                .group_by(Submission.status)
                .all()
            )

            # FIXED: Use proper enum comparison
            successful = sum(
                count
                for status, count in submission_counts
                if status in [SubmissionStatus.SUCCESS, SubmissionStatus.COMPLETED]
            )

            failed = sum(
                count
                for status, count in submission_counts
                if status == SubmissionStatus.FAILED
            )

            total = sum(count for status, count in submission_counts)

            # Get CAPTCHA stats
            captcha_encountered = (
                self.db.query(Submission)
                .filter(
                    and_(
                        Submission.campaign_id == campaign_id,
                        Submission.captcha_encountered == True,
                    )
                )
                .count()
            )

            captcha_solved = (
                self.db.query(Submission)
                .filter(
                    and_(
                        Submission.campaign_id == campaign_id,
                        Submission.captcha_solved == True,
                    )
                )
                .count()
            )

            success_rate = (successful / total * 100) if total > 0 else 0
            captcha_solve_rate = (
                (captcha_solved / captcha_encountered * 100)
                if captcha_encountered > 0
                else 0
            )

            # Handle missing campaign attributes safely
            total_urls = getattr(campaign, "total_urls", 0) or 0
            submitted_count = getattr(campaign, "submitted_count", 0) or 0
            failed_count = (
                getattr(campaign, "failed_count", 0)
                or getattr(campaign, "failed", 0)
                or 0
            )

            return CampaignAnalytics(
                campaign_id=str(campaign_id),
                campaign_name=campaign.name or "Unnamed Campaign",
                total_urls=total_urls,
                submitted_count=submitted_count,
                failed_count=failed_count,
                success_rate=round(success_rate, 2),
                captcha_encounters=captcha_encountered,
                captcha_solve_rate=round(captcha_solve_rate, 2),
            )

        except Exception as e:
            print(f"[ANALYTICS SERVICE] ❌ Failed to get campaign analytics: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve campaign analytics"
            )

    def get_system_analytics(self) -> SystemAnalytics:
        """Get system-wide analytics with error handling"""
        try:
            total_users = self.db.query(User).filter(User.is_active == True).count()

            # FIXED: Use proper campaign status enum
            active_campaigns = (
                self.db.query(Campaign)
                .filter(
                    Campaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.DRAFT])
                )
                .count()
            )

            # Get overall submission stats with proper enum handling
            total_submissions = self.db.query(Submission).count()

            successful_submissions = (
                self.db.query(Submission)
                .filter(
                    Submission.status.in_(
                        [SubmissionStatus.SUCCESS, SubmissionStatus.COMPLETED]
                    )
                )
                .count()
            )

            failed_submissions = (
                self.db.query(Submission)
                .filter(Submission.status == SubmissionStatus.FAILED)
                .count()
            )

            pending_submissions = (
                self.db.query(Submission)
                .filter(Submission.status == SubmissionStatus.PENDING)
                .count()
            )

            success_rate = (
                (successful_submissions / total_submissions * 100)
                if total_submissions > 0
                else 0
            )

            stats = SubmissionStats(
                total_submissions=total_submissions,
                successful_submissions=successful_submissions,
                failed_submissions=failed_submissions,
                pending_submissions=pending_submissions,
                success_rate=round(success_rate, 2),
            )

            # Get top performing campaigns with safe attribute access
            top_campaigns_query = (
                self.db.query(Campaign)
                .filter(Campaign.total_urls > 0)
                .order_by(desc(Campaign.submitted_count))
                .limit(5)
            )

            top_performing_campaigns = []
            for campaign in top_campaigns_query.all():
                try:
                    total_urls = getattr(campaign, "total_urls", 0) or 0
                    submitted_count = getattr(campaign, "submitted_count", 0) or 0
                    failed_count = (
                        getattr(campaign, "failed_count", 0)
                        or getattr(campaign, "failed", 0)
                        or 0
                    )

                    success_rate = (
                        (submitted_count / total_urls * 100) if total_urls > 0 else 0
                    )

                    top_performing_campaigns.append(
                        CampaignAnalytics(
                            campaign_id=str(campaign.id),
                            campaign_name=campaign.name or "Unnamed Campaign",
                            total_urls=total_urls,
                            submitted_count=submitted_count,
                            failed_count=failed_count,
                            success_rate=round(success_rate, 2),
                            captcha_encounters=0,  # Would need separate query
                            captcha_solve_rate=0,  # Would need separate query
                        )
                    )
                except Exception as campaign_error:
                    print(
                        f"[ANALYTICS SERVICE] ⚠️ Error processing campaign {campaign.id}: {campaign_error}"
                    )
                    continue

            return SystemAnalytics(
                total_users=total_users,
                active_campaigns=active_campaigns,
                total_submissions=total_submissions,
                stats=stats,
                top_performing_campaigns=top_performing_campaigns,
            )

        except Exception as e:
            print(f"[ANALYTICS SERVICE] ❌ Failed to get system analytics: {str(e)}")
            # Return zero stats instead of failing
            stats = SubmissionStats(
                total_submissions=0,
                successful_submissions=0,
                failed_submissions=0,
                pending_submissions=0,
                success_rate=0,
            )
            return SystemAnalytics(
                total_users=0,
                active_campaigns=0,
                total_submissions=0,
                stats=stats,
                top_performing_campaigns=[],
            )

    def get_daily_stats(
        self,
        user_id: Optional[uuid.UUID] = None,
        campaign_id: Optional[uuid.UUID] = None,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get daily submission statistics with proper enum handling"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            # FIXED: Use proper enum values in aggregation
            query = self.db.query(
                func.date(Submission.created_at).label("date"),
                func.count(Submission.id).label("total"),
                func.sum(
                    func.case(
                        [
                            (
                                Submission.status.in_(
                                    [
                                        SubmissionStatus.SUCCESS,
                                        SubmissionStatus.COMPLETED,
                                    ]
                                ),
                                1,
                            )
                        ],
                        else_=0,
                    )
                ).label("successful"),
                func.sum(
                    func.case(
                        [(Submission.status == SubmissionStatus.FAILED, 1)], else_=0
                    )
                ).label("failed"),
            ).filter(func.date(Submission.created_at) >= start_date)

            if user_id:
                query = query.filter(Submission.user_id == user_id)
            if campaign_id:
                query = query.filter(Submission.campaign_id == campaign_id)

            results = (
                query.group_by(func.date(Submission.created_at))
                .order_by(func.date(Submission.created_at))
                .all()
            )

            daily_stats = []
            for result in results:
                successful = result.successful or 0
                total = result.total or 0
                failed = result.failed or 0

                daily_stats.append(
                    {
                        "date": str(result.date),
                        "total": total,
                        "successful": successful,
                        "failed": failed,
                        "success_rate": round(
                            (successful / total * 100) if total > 0 else 0, 2
                        ),
                    }
                )

            print(f"[ANALYTICS SERVICE] 📈 Generated {len(daily_stats)} daily stats")
            return daily_stats

        except Exception as e:
            print(f"[ANALYTICS SERVICE] ❌ Failed to get daily stats: {str(e)}")
            return []

    def get_user_summary(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get a comprehensive user summary with safe error handling"""
        try:
            # Basic user info
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Campaign stats with safe attribute access
            campaigns = (
                self.db.query(Campaign).filter(Campaign.user_id == user_id).all()
            )

            total_campaigns = len(campaigns)
            total_urls = sum(getattr(c, "total_urls", 0) or 0 for c in campaigns)
            total_submitted = sum(
                getattr(c, "submitted_count", 0) or 0 for c in campaigns
            )
            total_failed = sum(
                (getattr(c, "failed_count", 0) or getattr(c, "failed", 0) or 0)
                for c in campaigns
            )

            # Submission stats
            submission_stats = self.get_user_analytics(user_id)

            return {
                "user_id": str(user_id),
                "email": user.email,
                "total_campaigns": total_campaigns,
                "total_urls": total_urls,
                "total_submitted": total_submitted,
                "total_failed": total_failed,
                "submission_stats": submission_stats.stats.dict(),
                "success_rate": submission_stats.stats.success_rate,
            }

        except Exception as e:
            print(f"[ANALYTICS SERVICE] ❌ Failed to get user summary: {str(e)}")
            return {
                "user_id": str(user_id),
                "error": "Failed to generate summary",
                "total_campaigns": 0,
                "total_urls": 0,
                "total_submitted": 0,
                "total_failed": 0,
                "success_rate": 0,
            }
