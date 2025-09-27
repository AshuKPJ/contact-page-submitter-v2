# app/services/submission_service.py
"""Submission service with clean separation of concerns."""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from fastapi import HTTPException

from app.models.submission import Submission, SubmissionStatus
from app.models.logs import SubmissionLog
from app.models.campaign import Campaign, CampaignStatus
from app.models.user_profile import UserProfile
from app.schemas.submission import SubmissionCreate, SubmissionUpdate

from app.utils.url_validator import URLValidator
from app.utils.status_converter import StatusConverter

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service for managing form submissions."""

    def __init__(self, db: Session):
        self.db = db
        self.url_validator = URLValidator()
        self.status_converter = StatusConverter()

    def create_submission(
        self, user_id: uuid.UUID, submission_data: SubmissionCreate
    ) -> Submission:
        """Create a new submission."""
        try:
            # Validate URL
            clean_url = self.url_validator.validate_and_normalize(submission_data.url)

            # Validate campaign
            if submission_data.campaign_id:
                self._validate_campaign(submission_data.campaign_id, user_id)
                self._check_duplicate_url(submission_data.campaign_id, clean_url)

            # Convert status
            status_enum = self.status_converter.to_enum(
                submission_data.status or "pending"
            )

            # Create submission
            submission = Submission(
                website_id=submission_data.website_id,
                campaign_id=submission_data.campaign_id,
                user_id=user_id,
                url=clean_url,
                contact_method=submission_data.contact_method,
                status=status_enum,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(submission)
            self.db.commit()
            self.db.refresh(submission)

            logger.info(f"Created submission {submission.id}")
            self._log_event(
                submission.id, "created", f"Submission created for {clean_url}"
            )

            return submission

        except ValueError as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create submission: {e}")
            raise HTTPException(status_code=500, detail="Failed to create submission")

    def get_submission(
        self, submission_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Submission]:
        """Get a submission by ID."""
        return (
            self.db.query(Submission)
            .filter(and_(Submission.id == submission_id, Submission.user_id == user_id))
            .first()
        )

    def update_submission(
        self,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
        submission_data: SubmissionUpdate,
    ) -> Optional[Submission]:
        """Update a submission."""
        try:
            submission = self.get_submission(submission_id, user_id)
            if not submission:
                return None

            # Check if modifiable
            if not self._can_modify(submission):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot modify submission in {submission.status.value} status",
                )

            # Apply updates
            update_data = submission_data.dict(exclude_unset=True)

            if "url" in update_data:
                update_data["url"] = self.url_validator.validate_and_normalize(
                    update_data["url"]
                )

            if "status" in update_data:
                update_data["status"] = self.status_converter.to_enum(
                    update_data["status"]
                )

            for field, value in update_data.items():
                setattr(submission, field, value)

            submission.updated_at = datetime.utcnow()

            # Set processing timestamps
            self._update_timestamps(submission)

            self.db.commit()
            self.db.refresh(submission)

            logger.info(f"Updated submission {submission_id}")
            return submission

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update submission: {e}")
            raise HTTPException(status_code=500, detail="Failed to update submission")

    def bulk_create_submissions(
        self, user_id: uuid.UUID, campaign_id: uuid.UUID, urls: List[str]
    ) -> Tuple[List[Submission], List[str]]:
        """Bulk create submissions."""
        try:
            # Validate campaign
            self._validate_campaign(campaign_id, user_id)

            # Get existing URLs
            existing_urls = self._get_existing_urls(campaign_id)

            submissions = []
            errors = []

            for i, url in enumerate(urls):
                try:
                    clean_url = self.url_validator.validate_and_normalize(url)

                    if clean_url in existing_urls:
                        errors.append(f"Row {i+1}: Duplicate URL")
                        continue

                    submission = Submission(
                        campaign_id=campaign_id,
                        user_id=user_id,
                        url=clean_url,
                        status=SubmissionStatus.PENDING,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    submissions.append(submission)
                    existing_urls.add(clean_url)

                except ValueError as e:
                    errors.append(f"Row {i+1}: {str(e)}")

            if submissions:
                self.db.add_all(submissions)
                self.db.commit()

                for submission in submissions:
                    self.db.refresh(submission)

            logger.info(f"Bulk created {len(submissions)} submissions")
            return submissions, errors

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to bulk create submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk create")

    def get_campaign_submissions(
        self,
        campaign_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        per_page: int = 10,
        **filters,
    ) -> Tuple[List[Submission], int]:
        """Get paginated campaign submissions."""
        try:
            # Validate campaign
            self._validate_campaign(campaign_id, user_id)

            # Build query
            query = self.db.query(Submission).filter(
                Submission.campaign_id == campaign_id
            )

            # Apply filters
            query = self._apply_filters(query, filters)

            # Get total and paginated results
            total = query.count()
            submissions = (
                query.order_by(desc(Submission.created_at))
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )

            return submissions, total

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get campaign submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get submissions")

    def get_user_profile_data(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Get user profile data for form filling."""
        try:
            profile = (
                self.db.query(UserProfile)
                .filter(UserProfile.user_id == user_id)
                .first()
            )

            if not profile:
                return self._get_default_profile()

            return {
                "first_name": profile.first_name or "John",
                "last_name": profile.last_name or "Doe",
                "email": profile.email or "contact@example.com",
                "phone_number": profile.phone_number or "",
                "company_name": profile.company_name or "",
                "subject": profile.subject or "Business Inquiry",
                "message": profile.message or "I am interested in your services.",
                "website_url": profile.website_url or "",
            }

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return self._get_default_profile()

    def retry_failed_submissions(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID, max_retries: int = 3
    ) -> Dict[str, Any]:
        """Retry failed submissions."""
        try:
            # Validate campaign
            self._validate_campaign(campaign_id, user_id)

            # Get failed submissions
            failed = (
                self.db.query(Submission)
                .filter(
                    and_(
                        Submission.campaign_id == campaign_id,
                        Submission.status == SubmissionStatus.FAILED,
                        Submission.retry_count < max_retries,
                    )
                )
                .all()
            )

            retried = 0
            skipped = 0

            for submission in failed:
                if self._is_permanent_error(submission.error_message):
                    skipped += 1
                    continue

                # Reset for retry
                submission.status = SubmissionStatus.PENDING
                submission.retry_count += 1
                submission.error_message = None
                submission.updated_at = datetime.utcnow()
                submission.processed_at = None
                submission.started_at = None

                retried += 1

                self._log_event(
                    submission.id,
                    "retry",
                    f"Retry attempt {submission.retry_count}/{max_retries}",
                )

            self.db.commit()

            return {
                "retried_count": retried,
                "skipped_count": skipped,
                "total_failed": len(failed),
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to retry submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to retry")

    # Private helper methods

    def _validate_campaign(self, campaign_id: uuid.UUID, user_id: uuid.UUID):
        """Validate campaign exists and belongs to user."""
        campaign = (
            self.db.query(Campaign)
            .filter(and_(Campaign.id == campaign_id, Campaign.user_id == user_id))
            .first()
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if campaign.status == CampaignStatus.COMPLETED:
            raise HTTPException(
                status_code=400, detail="Cannot modify completed campaign"
            )

        return campaign

    def _check_duplicate_url(self, campaign_id: uuid.UUID, url: str):
        """Check for duplicate URLs in campaign."""
        existing = (
            self.db.query(Submission)
            .filter(and_(Submission.campaign_id == campaign_id, Submission.url == url))
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400, detail="URL already exists in campaign"
            )

    def _get_existing_urls(self, campaign_id: uuid.UUID) -> set:
        """Get existing URLs for a campaign."""
        urls = (
            self.db.query(Submission.url)
            .filter(Submission.campaign_id == campaign_id)
            .all()
        )
        return {url[0] for url in urls}

    def _can_modify(self, submission: Submission) -> bool:
        """Check if submission can be modified."""
        return submission.status in [SubmissionStatus.PENDING, SubmissionStatus.FAILED]

    def _update_timestamps(self, submission: Submission):
        """Update submission timestamps based on status."""
        if submission.status == SubmissionStatus.PROCESSING:
            if not submission.started_at:
                submission.started_at = datetime.utcnow()

        elif submission.status in [SubmissionStatus.SUCCESS, SubmissionStatus.FAILED]:
            if not submission.processed_at:
                submission.processed_at = datetime.utcnow()

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to query."""
        if filters.get("status"):
            status_enum = self.status_converter.to_enum(filters["status"])
            query = query.filter(Submission.status == status_enum)

        if filters.get("search_query"):
            search = f"%{filters['search_query'].strip()}%"
            query = query.filter(
                or_(
                    Submission.url.ilike(search),
                    Submission.error_message.ilike(search),
                    Submission.email_extracted.ilike(search),
                )
            )

        return query

    def _is_permanent_error(self, error_message: Optional[str]) -> bool:
        """Check if error is permanent."""
        if not error_message:
            return False

        permanent_patterns = [
            "invalid url",
            "404",
            "403",
            "dns",
            "certificate",
            "ssl",
            "no forms found",
        ]

        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in permanent_patterns)

    def _log_event(
        self, submission_id: uuid.UUID, action: str, details: str, status: str = "info"
    ):
        """Log submission event."""
        try:
            submission = (
                self.db.query(Submission).filter(Submission.id == submission_id).first()
            )

            if submission:
                log = SubmissionLog(
                    campaign_id=submission.campaign_id,
                    submission_id=submission_id,
                    user_id=submission.user_id,
                    website_id=submission.website_id,
                    target_url=submission.url,
                    action=action,
                    details=details,
                    status=status,
                    timestamp=datetime.utcnow(),
                )

                self.db.add(log)
                self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def _get_default_profile(self) -> Dict[str, Any]:
        """Get default profile data."""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "contact@example.com",
            "phone_number": "",
            "company_name": "",
            "subject": "Business Inquiry",
            "message": "I am interested in your services.",
            "website_url": "",
        }
