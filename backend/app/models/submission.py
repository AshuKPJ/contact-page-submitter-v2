# app/models/submission.py
"""Submission model for tracking individual form submissions."""

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Text,
    Boolean,
    Integer,
    DateTime,
    Index,
    CheckConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


class SubmissionStatus(enum.Enum):
    """Submission status enum for Python code use."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"  # Used for successful submissions
    FAILED = "failed"
    RETRY = "retry"
    # Remove SUCCESS as it's redundant with COMPLETED


class Submission(Base):
    """Submission model for tracking individual form submissions."""

    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_website_id", "website_id"),
        Index("ix_submissions_user_id", "user_id"),
        Index("ix_submissions_campaign_id", "campaign_id"),
        Index("ix_submissions_status", "status"),
        Index("ix_submissions_success", "success"),
        Index("ix_submissions_submitted_at", "submitted_at"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'retry')",
            name="valid_submission_status",
        ),
        CheckConstraint(
            "contact_method IN ('form', 'email', 'phone', 'linkedin')",
            name="valid_contact_method",
        ),
        CheckConstraint("retry_count >= 0", name="non_negative_retry_count"),
        CheckConstraint("response_status >= 0", name="non_negative_response_status"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    website_id = Column(
        UUID(as_uuid=True),
        ForeignKey("websites.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Submission details
    url = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    contact_method = Column(String(50), nullable=True, default="form")

    # Results
    success = Column(Boolean, nullable=True)
    response_status = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Form data
    form_fields_sent = Column(JSONB, nullable=True)
    field_mapping_data = Column(JSONB, nullable=True)

    # Contact information
    email_extracted = Column(String(255), nullable=True)

    # Captcha handling
    captcha_encountered = Column(Boolean, nullable=True, default=False)
    captcha_solved = Column(Boolean, nullable=True, default=False)

    # Retry logic
    retry_count = Column(Integer, nullable=True, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    submitted_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    website = relationship("Website", back_populates="submissions")
    user = relationship("User", back_populates="submissions")
    campaign = relationship("Campaign", back_populates="submissions")
    submission_logs = relationship(
        "SubmissionLog", back_populates="submission", cascade="all, delete-orphan"
    )
    captcha_logs = relationship(
        "CaptchaLog", back_populates="submission", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Submission {self.id}: {self.status} ({self.contact_method})>"

    # ==================== Validators ====================

    @validates("status")
    def validate_status(self, key, status):
        """Validate submission status."""
        valid_statuses = [s.value for s in SubmissionStatus]
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return status

    @validates("contact_method")
    def validate_contact_method(self, key, method):
        """Validate contact method."""
        valid_methods = ["form", "email", "phone", "linkedin"]
        if method and method not in valid_methods:
            raise ValueError(
                f"Invalid contact method. Must be one of: {', '.join(valid_methods)}"
            )
        return method

    @validates("email_extracted")
    def validate_email(self, key, email):
        """Validate extracted email."""
        if email:
            email = email.lower().strip()
            if "@" not in email:
                raise ValueError("Invalid email format")
        return email

    @validates("retry_count")
    def validate_retry_count(self, key, count):
        """Validate retry count."""
        if count is not None and count < 0:
            raise ValueError("Retry count cannot be negative")
        return count

    # ==================== Properties ====================

    @property
    def status_enum(self) -> Optional[SubmissionStatus]:
        """Get status as enum if valid, otherwise return None."""
        try:
            return SubmissionStatus(self.status) if self.status else None
        except (ValueError, TypeError):
            return None

    @property
    def is_pending(self) -> bool:
        """Check if submission is pending."""
        return self.status == SubmissionStatus.PENDING.value

    @property
    def is_processing(self) -> bool:
        """Check if submission is processing."""
        return self.status == SubmissionStatus.PROCESSING.value

    @property
    def is_completed(self) -> bool:
        """Check if submission is completed (successful)."""
        return self.status == SubmissionStatus.COMPLETED.value

    @property
    def is_successful(self) -> bool:
        """Check if submission was successful."""
        return self.status == SubmissionStatus.COMPLETED.value and self.success == True

    @property
    def is_failed(self) -> bool:
        """Check if submission failed."""
        return self.status == SubmissionStatus.FAILED.value

    @property
    def needs_retry(self) -> bool:
        """Check if submission needs retry."""
        return self.status == SubmissionStatus.RETRY.value or (
            self.is_failed and self.retry_count < 3
        )

    @property
    def can_retry(self) -> bool:
        """Check if submission can be retried."""
        return self.retry_count < 3 and not self.success

    @property
    def processing_time(self) -> Optional[float]:
        """Calculate processing time in seconds."""
        if self.submitted_at and self.processed_at:
            return (self.processed_at - self.submitted_at).total_seconds()
        return None

    @property
    def contact_method_display(self) -> str:
        """Get display name for contact method."""
        method_names = {
            "form": "Contact Form",
            "email": "Email Fallback",
            "phone": "Phone Contact",
            "linkedin": "LinkedIn Message",
        }
        return method_names.get(self.contact_method, self.contact_method)

    @property
    def was_captcha_solved(self) -> bool:
        """Check if captcha was encountered and solved."""
        return self.captcha_encountered and self.captcha_solved

    # ==================== Status Management ====================

    def set_status(self, status: Union[SubmissionStatus, str]) -> None:
        """Set submission status with validation."""
        if isinstance(status, SubmissionStatus):
            self.status = status.value
        else:
            # Validate string status
            if status not in [s.value for s in SubmissionStatus]:
                raise ValueError(f"Invalid status: {status}")
            self.status = status

    def start_processing(self) -> None:
        """Mark submission as processing."""
        self.set_status(SubmissionStatus.PROCESSING)
        self.submitted_at = datetime.utcnow()

    def mark_success(
        self, response_status: int = 200, response_data: Dict[str, Any] = None
    ) -> None:
        """Mark submission as successful."""
        self.set_status(SubmissionStatus.COMPLETED)
        self.success = True
        self.response_status = response_status
        self.processed_at = datetime.utcnow()
        self.error_message = None

    def mark_failure(self, error_message: str, response_status: int = None) -> None:
        """Mark submission as failed."""
        self.set_status(SubmissionStatus.FAILED)
        self.success = False
        self.error_message = error_message
        if response_status:
            self.response_status = response_status
        self.processed_at = datetime.utcnow()

    def mark_for_retry(self, error_message: str = None) -> None:
        """Mark submission for retry."""
        self.set_status(SubmissionStatus.RETRY)
        self.retry_count = (self.retry_count or 0) + 1
        if error_message:
            self.error_message = error_message

    def reset_for_retry(self) -> None:
        """Reset submission for retry."""
        if self.can_retry:
            self.set_status(SubmissionStatus.PENDING)
            self.submitted_at = None
            self.processed_at = None
            self.response_status = None

    def mark_captcha_encountered(self, captcha_type: str = None) -> None:
        """Mark that captcha was encountered."""
        self.captcha_encountered = True
        if captcha_type and self.field_mapping_data:
            self.field_mapping_data["captcha_type"] = captcha_type

    def mark_captcha_solved(self, solve_time: float = None) -> None:
        """Mark that captcha was solved."""
        self.captcha_solved = True
        if solve_time and self.field_mapping_data:
            self.field_mapping_data["captcha_solve_time"] = solve_time

    # ==================== Data Management ====================

    def set_form_data(self, form_data: Dict[str, Any]) -> None:
        """Set form fields data."""
        # Clean the data - remove None values and empty strings
        cleaned_data = {k: v for k, v in form_data.items() if v is not None and v != ""}
        self.form_fields_sent = cleaned_data

    def get_form_data(self) -> Dict[str, Any]:
        """Get form fields data."""
        return self.form_fields_sent or {}

    def set_field_mapping(self, mapping: Dict[str, Any]) -> None:
        """Set field mapping data."""
        self.field_mapping_data = mapping

    def get_field_mapping(self) -> Dict[str, Any]:
        """Get field mapping data."""
        return self.field_mapping_data or {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to field mapping data."""
        if not self.field_mapping_data:
            self.field_mapping_data = {}
        self.field_mapping_data[key] = value

    def extract_email_from_response(self, response_text: str) -> Optional[str]:
        """Extract email from response text."""
        import re

        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        matches = re.findall(email_pattern, response_text)
        if matches:
            self.email_extracted = matches[0].lower()
            return self.email_extracted
        return None

    # ==================== Statistics Methods ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get submission statistics."""
        return {
            "id": str(self.id),
            "website_id": str(self.website_id) if self.website_id else None,
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "status": self.status,
            "contact_method": self.contact_method,
            "contact_method_display": self.contact_method_display,
            "success": self.success,
            "response_status": self.response_status,
            "retry_count": self.retry_count,
            "captcha_encountered": self.captcha_encountered,
            "captcha_solved": self.captcha_solved,
            "processing_time": self.processing_time,
            "submitted_at": (
                self.submitted_at.isoformat() if self.submitted_at else None
            ),
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "created_at": self.created_at.isoformat(),
        }

    # ==================== Serialization ====================

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert submission to dictionary."""
        data = {
            "id": str(self.id),
            "website_id": str(self.website_id) if self.website_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "url": self.url,
            "status": self.status,
            "contact_method": self.contact_method,
            "contact_method_display": self.contact_method_display,
            "success": self.success,
            "response_status": self.response_status,
            "retry_count": self.retry_count,
            "captcha_encountered": self.captcha_encountered,
            "captcha_solved": self.captcha_solved,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "submitted_at": (
                self.submitted_at.isoformat() if self.submitted_at else None
            ),
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
        }

        if include_sensitive:
            data.update(
                {
                    "form_fields_sent": self.form_fields_sent,
                    "field_mapping_data": self.field_mapping_data,
                    "email_extracted": self.email_extracted,
                    "error_message": self.error_message,
                }
            )

        return data

    # ==================== Class Methods ====================

    @classmethod
    def find_pending(cls, db: Session, limit: int = 100) -> List["Submission"]:
        """Find pending submissions."""
        return (
            db.query(cls)
            .filter(cls.status == SubmissionStatus.PENDING.value)
            .order_by(cls.created_at.asc())
            .limit(limit)
            .all()
        )

    @classmethod
    def find_for_retry(cls, db: Session, limit: int = 50) -> List["Submission"]:
        """Find submissions that need retry."""
        return (
            db.query(cls)
            .filter(cls.status == SubmissionStatus.RETRY.value, cls.retry_count < 3)
            .order_by(cls.updated_at.asc())
            .limit(limit)
            .all()
        )

    @classmethod
    def find_by_campaign(
        cls, db: Session, campaign_id: UUID, status: str = None
    ) -> List["Submission"]:
        """Find submissions by campaign."""
        query = db.query(cls).filter(cls.campaign_id == campaign_id)
        if status:
            query = query.filter(cls.status == status)
        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def get_campaign_stats(cls, db: Session, campaign_id: UUID) -> Dict[str, Any]:
        """Get statistics for a campaign."""
        stats = (
            db.query(
                func.count(cls.id).label("total"),
                func.sum(func.case([(cls.success == True, 1)], else_=0)).label(
                    "successful"
                ),
                func.sum(func.case([(cls.success == False, 1)], else_=0)).label(
                    "failed"
                ),
                func.sum(
                    func.case(
                        [(cls.status == SubmissionStatus.PENDING.value, 1)], else_=0
                    )
                ).label("pending"),
                func.sum(
                    func.case([(cls.captcha_encountered == True, 1)], else_=0)
                ).label("captcha_count"),
                func.sum(
                    func.case([(cls.contact_method == "email", 1)], else_=0)
                ).label("email_fallback"),
            )
            .filter(cls.campaign_id == campaign_id)
            .first()
        )

        total = stats.total or 0
        return {
            "total": total,
            "successful": stats.successful or 0,
            "failed": stats.failed or 0,
            "pending": stats.pending or 0,
            "captcha_count": stats.captcha_count or 0,
            "email_fallback": stats.email_fallback or 0,
            "success_rate": (
                round((stats.successful or 0) / total * 100, 2) if total > 0 else 0.0
            ),
        }


# ==================== Event Listeners ====================


@event.listens_for(Submission, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Before insert event."""
    if not target.created_at:
        target.created_at = datetime.utcnow()
    if not target.updated_at:
        target.updated_at = datetime.utcnow()
    if not target.status:
        target.status = SubmissionStatus.PENDING.value
    if target.retry_count is None:
        target.retry_count = 0


@event.listens_for(Submission, "before_update")
def receive_before_update(mapper, connection, target):
    """Before update event."""
    target.updated_at = datetime.utcnow()
