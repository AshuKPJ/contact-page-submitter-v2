# app/models/website.py
"""Enhanced Website model with form analysis and captcha handling."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    ARRAY,
    Index,
    CheckConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


class WebsiteStatus:
    """Website processing status constants."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CaptchaDifficulty:
    """Captcha difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    IMPOSSIBLE = "impossible"


class Website(Base):
    """Enhanced Website model with comprehensive form and captcha analysis."""

    __tablename__ = "websites"
    __table_args__ = (
        Index("ix_websites_campaign_id", "campaign_id"),
        Index("ix_websites_user_id", "user_id"),
        Index("ix_websites_domain", "domain"),
        Index("ix_websites_status", "status"),
        CheckConstraint(
            "status IN ('pending', 'analyzing', 'processing', 'completed', 'failed', 'skipped')",
            name="valid_website_status",
        ),
        CheckConstraint(
            "captcha_difficulty IS NULL OR captcha_difficulty IN ('easy', 'medium', 'hard', 'very_hard', 'impossible')",
            name="valid_captcha_difficulty",
        ),
        CheckConstraint(
            "form_field_count IS NULL OR form_field_count >= 0",
            name="non_negative_field_count",
        ),
        CheckConstraint(
            "captcha_solution_time IS NULL OR captcha_solution_time >= 0",
            name="non_negative_solution_time",
        ),
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
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Website details
    domain = Column(String(255), nullable=True, index=True)
    contact_url = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, default="pending")
    failure_reason = Column(Text, nullable=True)

    # Form detection
    form_detected = Column(Boolean, nullable=True, default=False)
    form_type = Column(String(100), nullable=True)
    form_labels = Column(ARRAY(Text), nullable=True)
    form_field_count = Column(Integer, nullable=True)
    form_name_variants = Column(ARRAY(Text), nullable=True)
    form_field_types = Column(JSONB, nullable=True, default={})
    form_field_options = Column(JSONB, nullable=True, default={})
    question_answer_fields = Column(JSONB, nullable=True, default={})

    # Captcha information
    has_captcha = Column(Boolean, nullable=True, default=False)
    captcha_type = Column(String(100), nullable=True)
    captcha_difficulty = Column(Text, nullable=True)
    captcha_solution_time = Column(Integer, nullable=True)
    captcha_metadata = Column(JSONB, nullable=True, default={})

    # Proxy information
    requires_proxy = Column(Boolean, nullable=True, default=False)
    proxy_block_type = Column(Text, nullable=True)
    last_proxy_used = Column(Text, nullable=True)

    # Analysis metadata
    analysis_attempts = Column(Integer, nullable=True, default=0)
    last_analysis_at = Column(DateTime, nullable=True)
    analysis_confidence = Column(Integer, nullable=True)  # 0-100

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="websites")
    campaign = relationship("Campaign", back_populates="websites")
    submissions = relationship("Submission", back_populates="website", lazy="dynamic")
    submission_logs = relationship(
        "SubmissionLog", back_populates="website", lazy="dynamic"
    )
    logs = relationship("Log", back_populates="website", lazy="dynamic")

    def __repr__(self):
        return f"<Website {self.domain}: {self.status}>"

    # ==================== Validators ====================

    @validates("domain")
    def validate_domain(self, key, domain):
        """Validate and normalize domain."""
        if domain:
            # Remove protocol and path
            domain = domain.lower().strip()
            domain = domain.replace("http://", "").replace("https://", "")
            domain = domain.replace("www.", "")
            domain = domain.split("/")[0]

            # Basic domain validation
            if "." not in domain:
                raise ValueError("Invalid domain format")
            if len(domain) > 255:
                raise ValueError("Domain too long")
        return domain

    @validates("contact_url")
    def validate_contact_url(self, key, url):
        """Validate contact URL."""
        if url:
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            # Ensure URL matches domain
            if self.domain:
                parsed = urlparse(url)
                url_domain = parsed.netloc.replace("www.", "")
                if self.domain not in url_domain:
                    raise ValueError("Contact URL doesn't match website domain")
        return url

    @validates("status")
    def validate_status(self, key, status):
        """Validate website status."""
        valid_statuses = [
            "pending",
            "analyzing",
            "processing",
            "completed",
            "failed",
            "skipped",
        ]
        if status and status not in valid_statuses:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return status

    # ==================== Properties ====================

    @property
    def is_complete(self) -> bool:
        """Check if website analysis is complete."""
        return self.status in ["completed", "failed", "skipped"]

    @property
    def is_processable(self) -> bool:
        """Check if website can be processed."""
        return self.form_detected and not self.has_impossible_captcha

    @property
    def has_impossible_captcha(self) -> bool:
        """Check if captcha is impossible to solve."""
        return self.captcha_difficulty == "impossible"

    @property
    def needs_proxy(self) -> bool:
        """Check if website requires proxy."""
        return self.requires_proxy or bool(self.proxy_block_type)

    @hybrid_property
    def form_complexity_score(self) -> float:
        """Calculate form complexity score (0-100)."""
        score = 0.0

        # Base score from field count
        if self.form_field_count:
            if self.form_field_count <= 5:
                score += 20
            elif self.form_field_count <= 10:
                score += 40
            elif self.form_field_count <= 20:
                score += 60
            else:
                score += 80

        # Add for captcha
        if self.has_captcha:
            difficulty_scores = {
                "easy": 5,
                "medium": 10,
                "hard": 15,
                "very_hard": 20,
                "impossible": 30,
            }
            score += difficulty_scores.get(self.captcha_difficulty, 10)

        # Add for proxy requirement
        if self.requires_proxy:
            score += 10

        return min(score, 100)

    @property
    def submission_success_rate(self) -> float:
        """Calculate success rate for submissions to this website."""
        total = self.submissions.count()
        if total > 0:
            successful = self.submissions.filter_by(success=True).count()
            return round((successful / total) * 100, 2)
        return 0.0

    @property
    def full_url(self) -> str:
        """Get full URL with protocol."""
        if self.contact_url:
            return self.contact_url
        elif self.domain:
            return f"https://{self.domain}/contact"
        return ""

    @property
    def tld(self) -> Optional[str]:
        """Get top-level domain."""
        if self.domain:
            parts = self.domain.split(".")
            if len(parts) >= 2:
                return f".{parts[-1]}"
        return None

    # ==================== Form Analysis Methods ====================

    def update_form_analysis(
        self,
        form_detected: bool,
        form_type: Optional[str] = None,
        field_count: Optional[int] = None,
        field_types: Optional[Dict[str, str]] = None,
        field_labels: Optional[List[str]] = None,
    ) -> None:
        """Update form analysis results."""
        self.form_detected = form_detected
        self.form_type = form_type
        self.form_field_count = field_count

        if field_types:
            self.form_field_types = field_types

        if field_labels:
            self.form_labels = field_labels
            # Extract name variants from labels
            name_variants = []
            for label in field_labels:
                if "name" in label.lower():
                    name_variants.append(label)
            if name_variants:
                self.form_name_variants = name_variants

        self.last_analysis_at = datetime.utcnow()
        self.analysis_attempts += 1

    def get_form_field(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific form field."""
        result = {}

        if self.form_field_types and field_name in self.form_field_types:
            result["type"] = self.form_field_types[field_name]

        if self.form_field_options and field_name in self.form_field_options:
            result["options"] = self.form_field_options[field_name]

        if self.form_labels:
            for label in self.form_labels:
                if field_name.lower() in label.lower():
                    result["label"] = label
                    break

        return result if result else None

    def has_required_fields(self, required_fields: List[str]) -> bool:
        """Check if form has all required fields."""
        if not self.form_labels:
            return False

        form_labels_lower = [label.lower() for label in self.form_labels]
        for field in required_fields:
            field_lower = field.lower()
            if not any(field_lower in label for label in form_labels_lower):
                return False

        return True

    # ==================== Captcha Methods ====================

    def update_captcha_info(
        self,
        has_captcha: bool,
        captcha_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update captcha information."""
        self.has_captcha = has_captcha

        if captcha_type:
            self.captcha_type = captcha_type

        if difficulty:
            self.captcha_difficulty = difficulty

        if metadata:
            if not self.captcha_metadata:
                self.captcha_metadata = {}
            self.captcha_metadata.update(metadata)

    def estimate_captcha_solve_time(self) -> int:
        """Estimate time to solve captcha in seconds."""
        if not self.has_captcha:
            return 0

        base_times = {
            "easy": 5,
            "medium": 15,
            "hard": 30,
            "very_hard": 60,
            "impossible": 999,
        }

        base_time = base_times.get(self.captcha_difficulty, 15)

        # Adjust based on captcha type
        if self.captcha_type:
            if "recaptcha_v3" in self.captcha_type.lower():
                base_time = 2  # Automated
            elif "hcaptcha" in self.captcha_type.lower():
                base_time *= 1.5  # Usually harder

        return int(base_time)

    # ==================== Proxy Methods ====================

    def update_proxy_requirement(
        self,
        requires_proxy: bool,
        block_type: Optional[str] = None,
        proxy_used: Optional[str] = None,
    ) -> None:
        """Update proxy requirement information."""
        self.requires_proxy = requires_proxy

        if block_type:
            self.proxy_block_type = block_type

        if proxy_used:
            self.last_proxy_used = proxy_used

    def get_recommended_proxy_type(self) -> Optional[str]:
        """Get recommended proxy type based on block type."""
        if not self.requires_proxy:
            return None

        if self.proxy_block_type:
            if "cloudflare" in self.proxy_block_type.lower():
                return "residential"
            elif "geo" in self.proxy_block_type.lower():
                return "country-specific"
            elif "rate" in self.proxy_block_type.lower():
                return "rotating"

        return "datacenter"  # Default

    # ==================== Statistics Methods ====================

    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive website statistics."""
        from app.models.submission import Submission

        # Get submission stats
        submission_stats = (
            db.query(
                func.count(Submission.id).label("total"),
                func.sum(func.cast(Submission.success, Integer)).label("successful"),
                func.avg(Submission.retry_count).label("avg_retries"),
            )
            .filter(Submission.website_id == self.id)
            .first()
        )

        return {
            "id": str(self.id),
            "domain": self.domain,
            "status": self.status,
            "form_detected": self.form_detected,
            "form_type": self.form_type,
            "form_field_count": self.form_field_count,
            "form_complexity_score": self.form_complexity_score,
            "has_captcha": self.has_captcha,
            "captcha_type": self.captcha_type,
            "captcha_difficulty": self.captcha_difficulty,
            "requires_proxy": self.requires_proxy,
            "proxy_block_type": self.proxy_block_type,
            "total_submissions": submission_stats.total if submission_stats else 0,
            "successful_submissions": (
                submission_stats.successful if submission_stats else 0
            ),
            "success_rate": self.submission_success_rate,
            "avg_retry_count": (
                float(submission_stats.avg_retries or 0) if submission_stats else 0
            ),
            "analysis_attempts": self.analysis_attempts,
            "last_analysis_at": (
                self.last_analysis_at.isoformat() if self.last_analysis_at else None
            ),
        }

    # ==================== Serialization ====================

    def to_dict(self, include_analysis: bool = True) -> Dict[str, Any]:
        """Convert website to dictionary."""
        data = {
            "id": str(self.id),
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "domain": self.domain,
            "contact_url": self.contact_url,
            "status": self.status,
            "form_detected": self.form_detected,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_analysis:
            data.update(
                {
                    "form_type": self.form_type,
                    "form_field_count": self.form_field_count,
                    "form_labels": self.form_labels,
                    "form_field_types": self.form_field_types,
                    "form_complexity_score": self.form_complexity_score,
                    "has_captcha": self.has_captcha,
                    "captcha_type": self.captcha_type,
                    "captcha_difficulty": self.captcha_difficulty,
                    "requires_proxy": self.requires_proxy,
                    "proxy_block_type": self.proxy_block_type,
                    "failure_reason": self.failure_reason,
                    "analysis_attempts": self.analysis_attempts,
                    "analysis_confidence": self.analysis_confidence,
                }
            )

        return data

    # ==================== Class Methods ====================

    @classmethod
    def find_by_domain(cls, db: Session, domain: str) -> Optional["Website"]:
        """Find website by domain."""
        normalized_domain = (
            domain.lower()
            .replace("www.", "")
            .replace("http://", "")
            .replace("https://", "")
        )
        return db.query(cls).filter(cls.domain == normalized_domain).first()

    @classmethod
    def find_pending_analysis(cls, db: Session, limit: int = 10) -> List["Website"]:
        """Find websites pending analysis."""
        return (
            db.query(cls)
            .filter(cls.status.in_(["pending", "analyzing"]))
            .limit(limit)
            .all()
        )

    @classmethod
    def find_by_campaign(cls, db: Session, campaign_id: UUID) -> List["Website"]:
        """Find websites by campaign."""
        return db.query(cls).filter(cls.campaign_id == campaign_id).all()


# ==================== Event Listeners ====================


@event.listens_for(Website, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Before insert event."""
    if not target.created_at:
        target.created_at = datetime.utcnow()
    if not target.updated_at:
        target.updated_at = datetime.utcnow()
    if not target.status:
        target.status = "pending"
    # Normalize domain on insert
    if target.domain:
        target.domain = (
            target.domain.lower()
            .replace("www.", "")
            .replace("http://", "")
            .replace("https://", "")
            .split("/")[0]
        )


@event.listens_for(Website, "before_update")
def receive_before_update(mapper, connection, target):
    """Before update event."""
    target.updated_at = datetime.utcnow()
