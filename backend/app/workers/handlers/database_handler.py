# app/workers/handlers/database_handler.py
"""Database handlers for campaign processing."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.campaign import Campaign, CampaignStatus
from app.models.submission import Submission, SubmissionStatus


def mark_submission_processing(db: Session, submission_id: uuid.UUID):
    """Mark a submission as processing."""
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = SubmissionStatus.PROCESSING
            submission.updated_at = datetime.utcnow()
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def mark_submission_result(
    db: Session,
    submission_id: uuid.UUID,
    success: bool,
    method: Optional[str] = None,
    error_message: Optional[str] = None,
    email_extracted: Optional[str] = None,
):
    """Mark submission with result."""
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = (
                SubmissionStatus.COMPLETED if success else SubmissionStatus.FAILED
            )
            submission.success = success
            submission.method = method
            submission.error_message = error_message
            submission.email_extracted = email_extracted
            submission.updated_at = datetime.utcnow()
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def pending_for_campaign(db: Session, campaign_id: uuid.UUID) -> List[Submission]:
    """Get pending submissions for a campaign."""
    try:
        return (
            db.query(Submission)
            .filter(
                Submission.campaign_id == campaign_id,
                Submission.status == SubmissionStatus.PENDING,
            )
            .all()
        )
    except SQLAlchemyError as e:
        raise e


def update_campaign_status(
    db: Session, campaign_id: uuid.UUID, status: CampaignStatus, **additional_fields
):
    """Update campaign status and additional fields."""
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.status = status
            campaign.updated_at = datetime.utcnow()

            # Update additional fields
            for field, value in additional_fields.items():
                if hasattr(campaign, field):
                    setattr(campaign, field, value)

            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e


def get_campaign_by_id(db: Session, campaign_id: uuid.UUID) -> Optional[Campaign]:
    """Get campaign by ID."""
    try:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()
    except SQLAlchemyError as e:
        raise e


def update_campaign_progress(
    db: Session, campaign_id: uuid.UUID, processed: int, successful: int, failed: int
):
    """Update campaign progress stats."""
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.processed = processed
            campaign.successful = successful
            campaign.failed = failed
            campaign.updated_at = datetime.utcnow()
            db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e
