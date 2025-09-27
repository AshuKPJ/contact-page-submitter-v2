# app/models/logs.py
"""Comprehensive logging models for tracking system events and activities."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Text,
    DateTime,
    Float,
    Boolean,
    Index,
    CheckConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates, Session

from app.core.database import Base


class SubmissionLog(Base):
    """Log entries for submission activities and events."""

    __tablename__ = "submission_logs"
    __table_args__ = (
        Index("ix_submission_logs_campaign_id", "campaign_id"),
        Index("ix_submission_logs_user_id", "user_id"),
        Index("ix_submission_logs_website_id", "website_id"),
        Index("ix_submission_logs_submission_id", "submission_id"),
        Index("ix_submission_logs_timestamp", "timestamp"),
        Index("ix_submission_logs_action", "action"),
        CheckConstraint(
            "action IN ('created', 'started', 'completed', 'failed', 'retried', 'captcha_solved', 'email_fallback')",
            name="valid_submission_action",
        ),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    website_id = Column(
        UUID(as_uuid=True),
        ForeignKey("websites.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Log details
    target_url = Column(String, nullable=False)
    action = Column(String(100), nullable=True)
    status = Column(String, nullable=True)
    details = Column(Text, nullable=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="submission_logs")
    user = relationship("User", back_populates="submission_logs")
    website = relationship("Website")
    submission = relationship("Submission", back_populates="submission_logs")

    def __repr__(self):
        return f"<SubmissionLog {self.action}: {self.target_url}>"

    @validates("action")
    def validate_action(self, key, action):
        """Validate submission action."""
        valid_actions = [
            "created",
            "started",
            "completed",
            "failed",
            "retried",
            "captcha_solved",
            "email_fallback",
        ]
        if action and action not in valid_actions:
            raise ValueError(
                f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )
        return action

    @classmethod
    def log_action(
        cls,
        db: Session,
        campaign_id: UUID,
        target_url: str,
        action: str,
        user_id: UUID = None,
        website_id: UUID = None,
        submission_id: UUID = None,
        status: str = None,
        details: str = None,
    ) -> "SubmissionLog":
        """Create a new submission log entry."""
        log_entry = cls(
            campaign_id=campaign_id,
            user_id=user_id,
            website_id=website_id,
            submission_id=submission_id,
            target_url=target_url,
            action=action,
            status=status,
            details=details,
        )
        db.add(log_entry)
        db.flush()
        return log_entry


class CaptchaLog(Base):
    """Log entries for captcha solving activities."""

    __tablename__ = "captcha_logs"
    __table_args__ = (
        Index("ix_captcha_logs_submission_id", "submission_id"),
        Index("ix_captcha_logs_timestamp", "timestamp"),
        Index("ix_captcha_logs_captcha_type", "captcha_type"),
        CheckConstraint(
            "captcha_type IN ('recaptcha_v2', 'recaptcha_v3', 'hcaptcha', 'cloudflare', 'custom')",
            name="valid_captcha_type",
        ),
        CheckConstraint("solve_time >= 0", name="non_negative_solve_time"),
        CheckConstraint("dbc_balance >= 0", name="non_negative_balance"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    submission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Captcha details
    captcha_type = Column(String(100), nullable=True)
    solved = Column(Boolean, nullable=True, default=False)
    solve_time = Column(Float, nullable=True)  # seconds
    dbc_balance = Column(Float, nullable=True)  # remaining balance
    error = Column(Text, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="captcha_logs")

    def __repr__(self):
        return (
            f"<CaptchaLog {self.captcha_type}: {'Solved' if self.solved else 'Failed'}>"
        )

    @validates("captcha_type")
    def validate_captcha_type(self, key, captcha_type):
        """Validate captcha type."""
        valid_types = [
            "recaptcha_v2",
            "recaptcha_v3",
            "hcaptcha",
            "cloudflare",
            "custom",
        ]
        if captcha_type and captcha_type not in valid_types:
            raise ValueError(
                f"Invalid captcha type. Must be one of: {', '.join(valid_types)}"
            )
        return captcha_type

    @classmethod
    def log_captcha_attempt(
        cls,
        db: Session,
        submission_id: UUID,
        captcha_type: str,
        solved: bool = False,
        solve_time: float = None,
        dbc_balance: float = None,
        error: str = None,
    ) -> "CaptchaLog":
        """Create a new captcha log entry."""
        log_entry = cls(
            submission_id=submission_id,
            captcha_type=captcha_type,
            solved=solved,
            solve_time=solve_time,
            dbc_balance=dbc_balance,
            error=error,
        )
        db.add(log_entry)
        db.flush()
        return log_entry


class SystemLog(Base):
    """System-wide log entries for administrative and security events."""

    __tablename__ = "system_logs"
    __table_args__ = (
        Index("ix_system_logs_user_id", "user_id"),
        Index("ix_system_logs_timestamp", "timestamp"),
        Index("ix_system_logs_action", "action"),
        CheckConstraint(
            "action IN ('login', 'logout', 'password_reset', 'email_verified', 'subscription_changed', 'settings_updated', 'campaign_created', 'campaign_started', 'campaign_completed', 'admin_action')",
            name="valid_system_action",
        ),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Log details
    action = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="system_logs")

    def __repr__(self):
        return f"<SystemLog {self.action}: {self.user_id}>"

    @validates("action")
    def validate_action(self, key, action):
        """Validate system action."""
        valid_actions = [
            "login",
            "logout",
            "password_reset",
            "email_verified",
            "subscription_changed",
            "settings_updated",
            "campaign_created",
            "campaign_started",
            "campaign_completed",
            "admin_action",
        ]
        if action and action not in valid_actions:
            raise ValueError(
                f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )
        return action

    @validates("ip_address")
    def validate_ip_address(self, key, ip):
        """Validate IP address format."""
        if ip:
            import ipaddress

            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise ValueError("Invalid IP address format")
        return ip

    @classmethod
    def log_system_event(
        cls,
        db: Session,
        action: str,
        user_id: UUID = None,
        details: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> "SystemLog":
        """Create a new system log entry."""
        log_entry = cls(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log_entry)
        db.flush()
        return log_entry

    @classmethod
    def log_login(
        cls, db: Session, user_id: UUID, ip_address: str = None, user_agent: str = None
    ):
        """Log user login."""
        return cls.log_system_event(
            db, "login", user_id, ip_address=ip_address, user_agent=user_agent
        )

    @classmethod
    def log_logout(cls, db: Session, user_id: UUID, ip_address: str = None):
        """Log user logout."""
        return cls.log_system_event(db, "logout", user_id, ip_address=ip_address)


class Log(Base):
    """General application logs with structured context."""

    __tablename__ = "logs"
    __table_args__ = (
        Index("ix_logs_user_id", "user_id"),
        Index("ix_logs_campaign_id", "campaign_id"),
        Index("ix_logs_website_id", "website_id"),
        Index("ix_logs_organization_id", "organization_id"),
        Index("ix_logs_level", "level"),
        Index("ix_logs_timestamp", "timestamp"),
        CheckConstraint(
            "level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name="valid_log_level",
        ),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    website_id = Column(
        UUID(as_uuid=True),
        ForeignKey("websites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Log details
    level = Column(String(20), nullable=True, default="INFO")
    message = Column(Text, nullable=False)
    context = Column(JSONB, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="logs")
    campaign = relationship("Campaign", back_populates="logs")
    website = relationship("Website", back_populates="logs")

    def __repr__(self):
        return f"<Log {self.level}: {self.message[:50]}>"

    @validates("level")
    def validate_level(self, key, level):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level and level not in valid_levels:
            raise ValueError(
                f"Invalid log level. Must be one of: {', '.join(valid_levels)}"
            )
        return level

    @classmethod
    def create_log(
        cls,
        db: Session,
        message: str,
        level: str = "INFO",
        user_id: UUID = None,
        campaign_id: UUID = None,
        website_id: UUID = None,
        organization_id: UUID = None,
        context: Dict[str, Any] = None,
    ) -> "Log":
        """Create a new log entry."""
        log_entry = cls(
            message=message,
            level=level,
            user_id=user_id,
            campaign_id=campaign_id,
            website_id=website_id,
            organization_id=organization_id,
            context=context,
        )
        db.add(log_entry)
        db.flush()
        return log_entry

    @classmethod
    def debug(cls, db: Session, message: str, **kwargs):
        """Create DEBUG log."""
        return cls.create_log(db, message, "DEBUG", **kwargs)

    @classmethod
    def info(cls, db: Session, message: str, **kwargs):
        """Create INFO log."""
        return cls.create_log(db, message, "INFO", **kwargs)

    @classmethod
    def warning(cls, db: Session, message: str, **kwargs):
        """Create WARNING log."""
        return cls.create_log(db, message, "WARNING", **kwargs)

    @classmethod
    def error(cls, db: Session, message: str, **kwargs):
        """Create ERROR log."""
        return cls.create_log(db, message, "ERROR", **kwargs)

    @classmethod
    def critical(cls, db: Session, message: str, **kwargs):
        """Create CRITICAL log."""
        return cls.create_log(db, message, "CRITICAL", **kwargs)

    @classmethod
    def get_recent_logs(
        cls,
        db: Session,
        limit: int = 100,
        level: str = None,
        user_id: UUID = None,
        campaign_id: UUID = None,
    ) -> List["Log"]:
        """Get recent log entries with optional filtering."""
        query = db.query(cls)

        if level:
            query = query.filter(cls.level == level)
        if user_id:
            query = query.filter(cls.user_id == user_id)
        if campaign_id:
            query = query.filter(cls.campaign_id == campaign_id)

        return query.order_by(cls.timestamp.desc()).limit(limit).all()


# ==================== Event Listeners ====================


@event.listens_for(SubmissionLog, "before_insert")
def receive_submission_log_before_insert(mapper, connection, target):
    """Before insert event for submission logs."""
    if not target.timestamp:
        target.timestamp = datetime.utcnow()


@event.listens_for(CaptchaLog, "before_insert")
def receive_captcha_log_before_insert(mapper, connection, target):
    """Before insert event for captcha logs."""
    if not target.timestamp:
        target.timestamp = datetime.utcnow()


@event.listens_for(SystemLog, "before_insert")
def receive_system_log_before_insert(mapper, connection, target):
    """Before insert event for system logs."""
    if not target.timestamp:
        target.timestamp = datetime.utcnow()


@event.listens_for(Log, "before_insert")
def receive_log_before_insert(mapper, connection, target):
    """Before insert event for general logs."""
    if not target.timestamp:
        target.timestamp = datetime.utcnow()
