# app/models/campaign.py
"""Campaign model updated to match database schema."""

import enum
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Float,
    JSON,
    Index,
    CheckConstraint,
    event,
    select,
    func,
    case,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


class CampaignStatus(enum.Enum):
    """Campaign status enum for Python code use."""

    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    STOPPED = "STOPPED"


class Campaign(Base):
    """Campaign model matching database schema."""

    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_campaigns_user_status", "user_id", "status"),
        Index("ix_campaigns_created_at", "created_at"),
        Index("ix_campaigns_status", "status"),
        CheckConstraint(
            "status IN ('DRAFT', 'QUEUED', 'RUNNING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PAUSED', 'CANCELLED', 'STOPPED')",
            name="valid_campaign_status",
        ),
        CheckConstraint("total_urls >= 0", name="non_negative_urls"),
        CheckConstraint("successful >= 0", name="non_negative_successful"),
        CheckConstraint("failed >= 0", name="non_negative_failed"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Campaign details
    name = Column(String(255), nullable=True)
    csv_filename = Column(String(255), nullable=True)
    file_name = Column(String(255), nullable=True)

    # Status as VARCHAR(50) - matching database
    status = Column(String(50), nullable=True, default="DRAFT")

    # Message and settings
    message = Column(Text, nullable=True)
    proxy = Column(String(255), nullable=True)
    use_captcha = Column(Boolean, nullable=True, default=True)

    # Statistics - matching database columns
    total_urls = Column(Integer, nullable=True, default=0)
    total_websites = Column(Integer, nullable=True, default=0)
    processed = Column(Integer, nullable=True, default=0)
    successful = Column(Integer, nullable=True, default=0)
    failed = Column(Integer, nullable=True, default=0)

    # Detailed counters
    submitted_count = Column(Integer, nullable=True, default=0)
    email_fallback = Column(Integer, nullable=True, default=0)
    failed_count = Column(Integer, nullable=True, default=0)
    no_form = Column(Integer, nullable=True, default=0)

    # Processing details
    processing_duration = Column(Float, nullable=True)  # DOUBLE PRECISION in DB
    error_message = Column(Text, nullable=True)

    # Settings (JSONB)
    settings = Column(JSON, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="campaigns")
    submissions = relationship(
        "Submission",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    websites = relationship("Website", back_populates="campaign", lazy="dynamic")
    submission_logs = relationship(
        "SubmissionLog", back_populates="campaign", lazy="dynamic"
    )
    logs = relationship("Log", back_populates="campaign", lazy="dynamic")

    def __repr__(self):
        return f"<Campaign {self.id}: {self.name} ({self.status})>"

    # ==================== Validators ====================

    @validates("status")
    def validate_status(self, key, status):
        """Validate campaign status."""
        valid_statuses = [s.value for s in CampaignStatus]
        if status and status not in valid_statuses:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return status

    @validates("name")
    def validate_name(self, key, name):
        """Validate and clean campaign name."""
        if name:
            name = name.strip()
            if len(name) > 255:
                raise ValueError("Campaign name must be 255 characters or less")
        return name

    # ==================== Properties ====================

    @property
    def status_enum(self) -> Optional[CampaignStatus]:
        """Get status as enum if valid, otherwise return None."""
        try:
            return CampaignStatus(self.status) if self.status else None
        except (ValueError, TypeError):
            return None

    @property
    def is_active(self) -> bool:
        """Check if campaign is currently active."""
        return self.status in ["RUNNING", "PROCESSING", "QUEUED"]

    @property
    def is_completed(self) -> bool:
        """Check if campaign is completed."""
        return self.status in ["COMPLETED", "FAILED", "CANCELLED", "STOPPED"]

    @property
    def can_start(self) -> bool:
        """Check if campaign can be started."""
        return self.status in ["DRAFT", "PAUSED", "STOPPED"]

    @property
    def can_pause(self) -> bool:
        """Check if campaign can be paused."""
        return self.status in ["RUNNING", "PROCESSING"]

    @property
    def can_cancel(self) -> bool:
        """Check if campaign can be cancelled."""
        return self.status in ["RUNNING", "PROCESSING", "QUEUED", "PAUSED"]

    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.total_urls or self.total_websites or 0
        if total > 0 and self.successful is not None:
            return round((self.successful / total) * 100, 2)
        return 0.0

    @success_rate.expression
    def success_rate(cls):
        """SQL expression for success rate."""
        total = func.coalesce(cls.total_urls, cls.total_websites, 0)
        return case((total > 0, (cls.successful * 100.0) / total), else_=0.0)

    @hybrid_property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        total = self.total_urls or self.total_websites or 0
        if total > 0 and self.processed is not None:
            return round((self.processed / total) * 100, 2)
        return 0.0

    @completion_rate.expression
    def completion_rate(cls):
        """SQL expression for completion rate."""
        total = func.coalesce(cls.total_urls, cls.total_websites, 0)
        return case((total > 0, (cls.processed * 100.0) / total), else_=0.0)

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        total = self.total_urls or self.total_websites or 0
        if total > 0 and self.failed is not None:
            return round((self.failed / total) * 100, 2)
        return 0.0

    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate time remaining for campaign completion."""
        if not self.is_active:
            return None

        remaining = (self.total_urls or self.total_websites or 0) - (
            self.processed or 0
        )
        if remaining <= 0:
            return timedelta(seconds=0)

        # Calculate processing speed
        if self.processing_duration and self.processed:
            speed = self.processed / self.processing_duration  # items per second
            if speed > 0:
                seconds_remaining = remaining / speed
                return timedelta(seconds=int(seconds_remaining))

        return None

    @property
    def processing_speed(self) -> float:
        """Calculate processing speed (items per minute)."""
        if self.processing_duration and self.processed:
            minutes = self.processing_duration / 60
            if minutes > 0:
                return round(self.processed / minutes, 2)
        return 0.0

    # ==================== Status Management ====================

    def set_status(self, status: Union[CampaignStatus, str]) -> None:
        """Set campaign status with validation."""
        if isinstance(status, CampaignStatus):
            self.status = status.value
        else:
            # Validate string status
            if status not in [s.value for s in CampaignStatus]:
                raise ValueError(f"Invalid status: {status}")
            self.status = status

        # Update timestamps based on status change
        if self.status == "RUNNING" and not self.started_at:
            self.started_at = datetime.utcnow()
        elif self.status in ["COMPLETED", "FAILED", "CANCELLED"]:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                self.processing_duration = (
                    self.completed_at - self.started_at
                ).total_seconds()

    def start(self) -> bool:
        """Start the campaign."""
        if not self.can_start:
            return False

        self.set_status("RUNNING")
        return True

    def pause(self) -> bool:
        """Pause the campaign."""
        if not self.can_pause:
            return False

        self.set_status("PAUSED")
        return True

    def cancel(self, reason: Optional[str] = None) -> bool:
        """Cancel the campaign."""
        if not self.can_cancel:
            return False

        self.set_status("CANCELLED")
        if reason:
            self.error_message = f"Cancelled: {reason}"
        return True

    def complete(self) -> None:
        """Mark campaign as completed."""
        if self.failed and self.failed > 0 and not self.successful:
            self.set_status("FAILED")
        else:
            self.set_status("COMPLETED")

    # ==================== Statistics Methods ====================

    def update_statistics(self, db: Session) -> None:
        """Update campaign statistics from submissions."""
        from app.models.submission import Submission

        # Count submissions by status
        stats = (
            db.query(
                func.count(Submission.id).label("total"),
                func.sum(case((Submission.success == True, 1), else_=0)).label(
                    "successful"
                ),
                func.sum(case((Submission.success == False, 1), else_=0)).label(
                    "failed"
                ),
                func.sum(case((Submission.status == "pending", 1), else_=0)).label(
                    "pending"
                ),
                func.sum(case((Submission.status == "processing", 1), else_=0)).label(
                    "processing"
                ),
                func.sum(
                    case((Submission.contact_method == "email", 1), else_=0)
                ).label("email_fallback"),
            )
            .filter(Submission.campaign_id == self.id)
            .first()
        )

        if stats:
            self.submitted_count = stats.total or 0
            self.successful = stats.successful or 0
            self.failed_count = stats.failed or 0
            self.email_fallback = stats.email_fallback or 0
            self.processed = (stats.successful or 0) + (stats.failed or 0)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive campaign statistics."""
        total = self.total_urls or self.total_websites or 0

        return {
            "id": str(self.id),
            "name": self.name,
            "status": self.status,
            "total_items": total,
            "processed": self.processed or 0,
            "successful": self.successful or 0,
            "failed": self.failed or 0,
            "pending": total - (self.processed or 0),
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "completion_rate": self.completion_rate,
            "email_fallback": self.email_fallback or 0,
            "no_form": self.no_form or 0,
            "processing_speed": self.processing_speed,
            "processing_duration": self.processing_duration,
            "estimated_time_remaining": (
                self.estimated_time_remaining.total_seconds()
                if self.estimated_time_remaining
                else None
            ),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    # ==================== Settings Management ====================

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        if not self.settings:
            return default
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value."""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update multiple settings."""
        if not self.settings:
            self.settings = {}
        self.settings.update(settings)

    # ==================== Serialization ====================

    def to_dict(self, include_stats: bool = True) -> Dict[str, Any]:
        """Convert campaign to dictionary."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "name": self.name,
            "status": self.status,
            "csv_filename": self.csv_filename,
            "file_name": self.file_name,
            "message": self.message,
            "proxy": self.proxy,
            "use_captcha": self.use_captcha,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

        if include_stats:
            data.update(
                {
                    "total_urls": self.total_urls,
                    "total_websites": self.total_websites,
                    "processed": self.processed or 0,
                    "successful": self.successful or 0,
                    "failed": self.failed or 0,
                    "submitted_count": self.submitted_count or 0,
                    "email_fallback": self.email_fallback or 0,
                    "failed_count": self.failed_count or 0,
                    "no_form": self.no_form or 0,
                    "success_rate": self.success_rate,
                    "completion_rate": self.completion_rate,
                    "processing_duration": self.processing_duration,
                    "processing_speed": self.processing_speed,
                    "error_message": self.error_message,
                }
            )

        return data

    # ==================== Class Methods ====================

    @classmethod
    def find_active(
        cls, db: Session, user_id: Optional[UUID] = None
    ) -> List["Campaign"]:
        """Find active campaigns."""
        query = db.query(cls).filter(
            cls.status.in_(["RUNNING", "PROCESSING", "QUEUED"])
        )
        if user_id:
            query = query.filter(cls.user_id == user_id)
        return query.all()

    @classmethod
    def find_by_user(
        cls, db: Session, user_id: UUID, limit: int = 10
    ) -> List["Campaign"]:
        """Find campaigns by user."""
        return (
            db.query(cls)
            .filter(cls.user_id == user_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
            .all()
        )


# ==================== Event Listeners ====================


@event.listens_for(Campaign, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Before insert event."""
    if not target.created_at:
        target.created_at = datetime.utcnow()
    if not target.updated_at:
        target.updated_at = datetime.utcnow()
    if not target.status:
        target.status = "DRAFT"


@event.listens_for(Campaign, "before_update")
def receive_before_update(mapper, connection, target):
    """Before update event."""
    target.updated_at = datetime.utcnow()
