# app/services/campaign_service.py
"""Campaign management service."""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException

from app.models.campaign import Campaign, CampaignStatus
from app.models.submission import Submission, SubmissionStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for managing campaigns."""

    def __init__(self, db: Session):
        self.db = db

    def create_campaign(
        self, user_id: uuid.UUID, campaign_data: CampaignCreate
    ) -> Campaign:
        """Create a new campaign."""
        try:
            campaign = Campaign(
                user_id=user_id,
                name=self._validate_name(campaign_data.name),
                message=campaign_data.message,
                status=CampaignStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)

            logger.info(f"Created campaign {campaign.id}")
            return campaign

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create campaign: {e}")
            raise HTTPException(status_code=500, detail="Failed to create campaign")

    def get_campaign(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Campaign]:
        """Get a campaign by ID."""
        return (
            self.db.query(Campaign)
            .filter(and_(Campaign.id == campaign_id, Campaign.user_id == user_id))
            .first()
        )

    def update_campaign(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID, campaign_data: CampaignUpdate
    ) -> Optional[Campaign]:
        """Update a campaign."""
        try:
            campaign = self.get_campaign(campaign_id, user_id)
            if not campaign:
                return None

            if not self._can_modify(campaign):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot modify campaign in {campaign.status.value} status",
                )

            update_data = campaign_data.dict(exclude_unset=True)

            for field, value in update_data.items():
                setattr(campaign, field, value)

            campaign.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(campaign)

            logger.info(f"Updated campaign {campaign_id}")
            return campaign

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update campaign: {e}")
            raise HTTPException(status_code=500, detail="Failed to update campaign")

    def delete_campaign(self, campaign_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a campaign."""
        try:
            campaign = self.get_campaign(campaign_id, user_id)
            if not campaign:
                return False

            if campaign.status == CampaignStatus.ACTIVE:
                raise HTTPException(
                    status_code=400, detail="Cannot delete active campaign"
                )

            # Delete submissions
            self.db.query(Submission).filter(
                Submission.campaign_id == campaign_id
            ).delete()

            # Delete campaign
            self.db.delete(campaign)
            self.db.commit()

            logger.info(f"Deleted campaign {campaign_id}")
            return True

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete campaign: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete campaign")

    def get_user_campaigns(
        self, user_id: uuid.UUID, page: int = 1, per_page: int = 10
    ) -> tuple[List[Campaign], int]:
        """Get user campaigns."""
        query = self.db.query(Campaign).filter(Campaign.user_id == user_id)

        total = query.count()
        campaigns = (
            query.order_by(Campaign.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return campaigns, total

    def _validate_name(self, name: str) -> str:
        """Validate campaign name."""
        if not name or not name.strip():
            raise ValueError("Campaign name is required")

        clean_name = name.strip()
        if len(clean_name) > 255:
            raise ValueError("Campaign name too long")

        return clean_name

    def _can_modify(self, campaign: Campaign) -> bool:
        """Check if campaign can be modified."""
        return campaign.status in [
            CampaignStatus.DRAFT,
            CampaignStatus.PAUSED,
            CampaignStatus.FAILED,
        ]
