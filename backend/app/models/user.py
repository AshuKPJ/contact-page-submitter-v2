# app/models/user.py
"""Enhanced User model with comprehensive security, subscription management, and business logic."""

from __future__ import annotations

import uuid
import secrets
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Integer,
    Index,
    CheckConstraint,
    event,
    select,
    func,
    and_,
    or_,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.core.security import hash_password, verify_password

if TYPE_CHECKING:
    from app.models.subscription import Subscription, SubscriptionPlan
    from app.models.user_profile import UserProfile
    from app.models.settings import Settings
    from app.models.campaign import Campaign


class User(Base):
    """Enhanced User model with comprehensive security, subscription, and business logic."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_role", "role"),
        CheckConstraint(
            "role IN ('user', 'admin', 'owner', 'moderator')", name="valid_role"
        ),
        CheckConstraint(
            r"email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'",
            name="valid_email",
        ),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)

    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_image_url = Column(Text, nullable=True)

    # Role and Status
    role = Column(String(20), nullable=True, default="user")
    is_active = Column(Boolean, nullable=True, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)

    # Subscription
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True
    )
    subscription_status = Column(String(50), nullable=True)
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    campaigns = relationship(
        "Campaign", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    submissions = relationship("Submission", back_populates="user", lazy="dynamic")
    user_profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    websites = relationship("Website", back_populates="user", lazy="dynamic")
    settings = relationship(
        "Settings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    subscriptions = relationship("Subscription", back_populates="user", lazy="dynamic")
    logs = relationship("Log", back_populates="user", lazy="dynamic")
    system_logs = relationship("SystemLog", back_populates="user", lazy="dynamic")
    submission_logs = relationship(
        "SubmissionLog", back_populates="user", lazy="dynamic"
    )

    def __repr__(self):
        return f"<User {self.email}>"

    # ==================== Validators ====================

    @validates("email")
    def validate_email(self, key, email):
        """Validate and normalize email."""
        if not email:
            raise ValueError("Email is required")
        email = email.lower().strip()
        if "@" not in email:
            raise ValueError("Invalid email format")
        return email

    @validates("role")
    def validate_role(self, key, role):
        """Validate user role."""
        valid_roles = ["user", "admin", "owner", "moderator"]
        if role and role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return role

    # ==================== Properties ====================

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email.split("@")[0]

    @property
    def display_name(self) -> str:
        """Get user's display name (full name or email username)."""
        return (
            self.full_name
            if (self.first_name or self.last_name)
            else self.email.split("@")[0]
        )

    @property
    def is_admin(self) -> bool:
        """Check if user is admin or owner."""
        return self.role in ["admin", "owner"]

    @property
    def is_owner(self) -> bool:
        """Check if user is owner."""
        return self.role == "owner"

    @property
    def is_moderator(self) -> bool:
        """Check if user is moderator."""
        return self.role == "moderator"

    @property
    def is_premium_user(self) -> bool:
        """Check if user has premium features."""
        return self.is_admin or self.is_subscribed

    @property
    def is_subscribed(self) -> bool:
        """Check if user has active subscription."""
        if not self.subscription_status:
            return False
        if self.subscription_status != "active":
            return False
        if self.subscription_end:
            return datetime.utcnow() < self.subscription_end
        return True

    @property
    def subscription_days_remaining(self) -> Optional[int]:
        """Get days remaining in subscription."""
        if not self.subscription_end or not self.is_subscribed:
            return None
        remaining = self.subscription_end - datetime.utcnow()
        return max(0, remaining.days)

    @property
    def is_subscription_expiring_soon(self, days: int = 7) -> bool:
        """Check if subscription is expiring soon."""
        if not self.subscription_days_remaining:
            return False
        return self.subscription_days_remaining <= days

    @property
    def days_since_registration(self) -> int:
        """Get days since registration."""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

    @property
    def account_age_display(self) -> str:
        """Get formatted account age."""
        days = self.days_since_registration
        if days < 30:
            return f"{days} days"
        elif days < 365:
            months = days // 30
            return f"{months} months"
        else:
            years = days // 365
            return f"{years} years"

    @property
    def is_new_user(self, days: int = 7) -> bool:
        """Check if user is new (registered within specified days)."""
        return self.days_since_registration <= days

    @hybrid_property
    def campaign_count(self) -> int:
        """Get total campaign count."""
        return self.campaigns.count()

    @campaign_count.expression
    def campaign_count(cls):
        """SQL expression for campaign count."""
        from app.models.campaign import Campaign

        return (
            select(func.count(Campaign.id))
            .where(Campaign.user_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def submission_count(self) -> int:
        """Get total submission count."""
        return self.submissions.count()

    @submission_count.expression
    def submission_count(cls):
        """SQL expression for submission count."""
        from app.models.submission import Submission

        return (
            select(func.count(Submission.id))
            .where(Submission.user_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def website_count(self) -> int:
        """Get total website count."""
        return self.websites.count()

    @website_count.expression
    def website_count(cls):
        """SQL expression for website count."""
        from app.models.website import Website

        return (
            select(func.count(Website.id))
            .where(Website.user_id == cls.id)
            .scalar_subquery()
        )

    # ==================== Authentication Methods ====================

    def set_password(self, password: str) -> None:
        """Set user password (hashed)."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        self.hashed_password = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        if not password or not self.hashed_password:
            return False
        return verify_password(password, self.hashed_password)

    def generate_password_reset_token(self) -> str:
        """Generate password reset token."""
        token = secrets.token_urlsafe(32)
        # Store token with expiration in user profile or separate table
        return token

    def generate_email_verification_token(self) -> str:
        """Generate email verification token."""
        token = secrets.token_urlsafe(32)
        # Store token in user profile or separate table
        return token

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.is_verified = True

    def deactivate_account(self, reason: str = None) -> None:
        """Deactivate user account."""
        self.is_active = False
        # Log the deactivation
        # SystemLog would need db session, so this should be called from service layer

    def reactivate_account(self) -> None:
        """Reactivate user account."""
        self.is_active = True

    # ==================== Subscription Methods ====================

    def get_current_subscription(self, db: Session) -> Optional["Subscription"]:
        """Get user's current active subscription."""
        from app.models.subscription import Subscription

        return (
            db.query(Subscription)
            .filter(Subscription.user_id == self.id, Subscription.status == "active")
            .first()
        )

    def get_subscription_plan(self, db: Session) -> Optional["SubscriptionPlan"]:
        """Get user's current subscription plan."""
        if not self.plan_id:
            return None
        from app.models.subscription import SubscriptionPlan

        return (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.id == self.plan_id)
            .first()
        )

    def can_create_campaigns(self, db: Session) -> bool:
        """Check if user can create campaigns."""
        if not self.is_active:
            return False
        if self.is_admin:
            return True
        return self.is_subscribed

    def can_create_websites(self, db: Session, additional_count: int = 1) -> bool:
        """Check if user can create more websites."""
        if not self.is_active:
            return False
        if self.is_admin:
            return True

        plan = self.get_subscription_plan(db)
        if not plan:
            return False

        current_count = self.website_count
        return plan.can_create_websites(current_count + additional_count - 1)

    def can_submit_today(self, db: Session, additional_count: int = 1) -> bool:
        """Check if user can submit more today."""
        if not self.is_active:
            return False
        if self.is_admin:
            return True

        plan = self.get_subscription_plan(db)
        if not plan:
            return False

        today_count = self.get_today_submission_count(db)
        return plan.can_submit_today(today_count + additional_count - 1)

    def get_usage_limits(self, db: Session) -> Dict[str, Any]:
        """Get user's usage limits and current usage."""
        plan = self.get_subscription_plan(db)
        if not plan:
            return {
                "websites": {"limit": 0, "used": 0, "remaining": 0, "unlimited": False},
                "daily_submissions": {
                    "limit": 0,
                    "used": 0,
                    "remaining": 0,
                    "unlimited": False,
                },
            }

        website_count = self.website_count
        today_submissions = self.get_today_submission_count(db)

        return {
            "websites": {
                "limit": plan.max_websites,
                "used": website_count,
                "remaining": plan.get_websites_remaining(website_count),
                "unlimited": plan.unlimited_websites,
            },
            "daily_submissions": {
                "limit": plan.max_submissions_per_day,
                "used": today_submissions,
                "remaining": plan.get_submissions_remaining_today(today_submissions),
                "unlimited": plan.unlimited_submissions,
            },
        }

    # ==================== Activity Methods ====================

    def update_last_activity(self) -> None:
        """Update user's last activity timestamp."""
        # This would need to be stored in a separate field if we want to track it
        # For now, we update the updated_at field
        self.updated_at = datetime.utcnow()

    def get_today_submission_count(self, db: Session) -> int:
        """Get number of submissions made today."""
        from app.models.submission import Submission

        today = date.today()
        return (
            db.query(func.count(Submission.id))
            .filter(
                Submission.user_id == self.id, func.date(Submission.created_at) == today
            )
            .scalar()
            or 0
        )

    def get_this_month_submission_count(self, db: Session) -> int:
        """Get number of submissions made this month."""
        from app.models.submission import Submission

        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return (
            db.query(func.count(Submission.id))
            .filter(Submission.user_id == self.id, Submission.created_at >= month_start)
            .scalar()
            or 0
        )

    def get_active_campaigns_count(self, db: Session) -> int:
        """Get number of active campaigns."""
        from app.models.campaign import Campaign

        return self.campaigns.filter(
            Campaign.status.in_(["RUNNING", "PROCESSING", "QUEUED"])
        ).count()

    def get_recent_activity(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent activity."""
        from app.models.logs import SystemLog

        recent_logs = (
            db.query(SystemLog)
            .filter(SystemLog.user_id == self.id)
            .order_by(SystemLog.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "action": log.action,
                "details": log.details,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "ip_address": log.ip_address,
            }
            for log in recent_logs
        ]

    # ==================== Profile Methods ====================

    def get_or_create_profile(self, db: Session) -> "UserProfile":
        """Get or create user profile."""
        if self.user_profile:
            return self.user_profile

        from app.models.user_profile import UserProfile

        profile = UserProfile(user_id=self.id)
        db.add(profile)
        db.flush()
        return profile

    def get_or_create_settings(self, db: Session) -> "Settings":
        """Get or create user settings."""
        if self.settings:
            return self.settings

        from app.models.settings import Settings

        settings = Settings(user_id=self.id)
        db.add(settings)
        db.flush()
        return settings

    def update_profile_from_dict(self, db: Session, data: Dict[str, Any]) -> None:
        """Update user profile from dictionary data."""
        profile = self.get_or_create_profile(db)
        for key, value in data.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)

    # ==================== Statistics Methods ====================

    def get_comprehensive_statistics(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        from app.models.campaign import Campaign
        from app.models.submission import Submission

        # Basic counts
        total_campaigns = self.campaigns.count()
        active_campaigns = self.get_active_campaigns_count(db)
        total_submissions = self.submissions.count()
        successful_submissions = self.submissions.filter(
            Submission.success == True
        ).count()
        failed_submissions = self.submissions.filter(
            Submission.success == False
        ).count()

        # Time-based stats
        today_submissions = self.get_today_submission_count(db)
        month_submissions = self.get_this_month_submission_count(db)

        # Success rates
        success_rate = 0.0
        if total_submissions > 0:
            success_rate = round((successful_submissions / total_submissions) * 100, 2)

        # Usage limits
        usage_limits = self.get_usage_limits(db)

        return {
            "user_info": {
                "id": str(self.id),
                "email": self.email,
                "display_name": self.display_name,
                "role": self.role,
                "is_verified": self.is_verified,
                "is_subscribed": self.is_subscribed,
                "account_age_days": self.days_since_registration,
                "account_age_display": self.account_age_display,
                "is_new_user": self.is_new_user(),
            },
            "usage_stats": {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "total_submissions": total_submissions,
                "successful_submissions": successful_submissions,
                "failed_submissions": failed_submissions,
                "success_rate": success_rate,
                "today_submissions": today_submissions,
                "month_submissions": month_submissions,
                "total_websites": self.website_count,
            },
            "subscription_info": {
                "status": self.subscription_status,
                "days_remaining": self.subscription_days_remaining,
                "is_expiring_soon": self.is_subscription_expiring_soon,
                "plan_id": str(self.plan_id) if self.plan_id else None,
            },
            "usage_limits": usage_limits,
        }

    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get basic user statistics (backward compatibility)."""
        stats = self.get_comprehensive_statistics(db)
        return {
            **stats["usage_stats"],
            "account_age_days": stats["user_info"]["account_age_days"],
            "is_verified": stats["user_info"]["is_verified"],
            "is_subscribed": stats["user_info"]["is_subscribed"],
        }

    # ==================== Campaign Methods ====================

    def get_campaigns_by_status(self, db: Session, status: str) -> List["Campaign"]:
        """Get campaigns by status."""
        from app.models.campaign import Campaign

        return self.campaigns.filter(Campaign.status == status).all()

    def get_recent_campaigns(self, db: Session, limit: int = 5) -> List["Campaign"]:
        """Get user's recent campaigns."""
        from app.models.campaign import Campaign

        return self.campaigns.order_by(Campaign.created_at.desc()).limit(limit).all()

    def can_start_new_campaign(self, db: Session) -> tuple[bool, str]:
        """Check if user can start a new campaign with reason."""
        if not self.is_active:
            return False, "Account is not active"

        if not self.is_verified:
            return False, "Email not verified"

        if not self.can_create_campaigns(db):
            return False, "Subscription required to create campaigns"

        active_campaigns = self.get_active_campaigns_count(db)
        max_active = 5 if self.is_premium_user else 1

        if active_campaigns >= max_active:
            return False, f"Maximum {max_active} active campaigns allowed"

        return True, "Can create campaign"

    # ==================== Serialization ====================

    def to_dict(
        self,
        include_sensitive: bool = False,
        include_stats: bool = False,
        db: Session = None,
    ) -> Dict[str, Any]:
        """Convert user to dictionary with flexible options."""
        data = {
            "id": str(self.id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "profile_image_url": self.profile_image_url,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "is_premium_user": self.is_premium_user,
            "is_subscribed": self.is_subscribed,
            "subscription_status": self.subscription_status,
            "account_age_display": self.account_age_display,
            "is_new_user": self.is_new_user(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_sensitive:
            data.update(
                {
                    "plan_id": str(self.plan_id) if self.plan_id else None,
                    "subscription_start": (
                        self.subscription_start.isoformat()
                        if self.subscription_start
                        else None
                    ),
                    "subscription_end": (
                        self.subscription_end.isoformat()
                        if self.subscription_end
                        else None
                    ),
                    "subscription_days_remaining": self.subscription_days_remaining,
                    "is_subscription_expiring_soon": self.is_subscription_expiring_soon,
                }
            )

        if include_stats and db:
            stats = self.get_comprehensive_statistics(db)
            data.update(
                {
                    "statistics": stats["usage_stats"],
                    "usage_limits": stats["usage_limits"],
                }
            )

        return data

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert user to public dictionary (safe for external APIs)."""
        return {
            "id": str(self.id),
            "display_name": self.display_name,
            "role": self.role if self.role in ["admin", "moderator"] else "user",
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    # ==================== Class Methods ====================

    @classmethod
    def find_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """Find user by email."""
        return db.query(cls).filter(cls.email == email.lower()).first()

    @classmethod
    def find_active(cls, db: Session) -> List["User"]:
        """Find all active users."""
        return db.query(cls).filter(cls.is_active == True).all()

    @classmethod
    def find_admins(cls, db: Session) -> List["User"]:
        """Find all admin users."""
        return db.query(cls).filter(cls.role.in_(["admin", "owner"])).all()

    @classmethod
    def find_unverified(cls, db: Session, older_than_days: int = 7) -> List["User"]:
        """Find unverified users older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        return (
            db.query(cls)
            .filter(cls.is_verified == False, cls.created_at < cutoff_date)
            .all()
        )

    @classmethod
    def find_expiring_subscriptions(cls, db: Session, days: int = 7) -> List["User"]:
        """Find users with subscriptions expiring soon."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        return (
            db.query(cls)
            .filter(
                cls.subscription_status == "active",
                cls.subscription_end <= cutoff_date,
                cls.subscription_end > datetime.utcnow(),
            )
            .all()
        )

    @classmethod
    def find_inactive_users(cls, db: Session, days: int = 30) -> List["User"]:
        """Find users inactive for specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(cls)
            .filter(cls.is_active == True, cls.updated_at < cutoff_date)
            .all()
        )

    @classmethod
    def get_user_count_by_role(cls, db: Session) -> Dict[str, int]:
        """Get user count by role."""
        result = db.query(cls.role, func.count(cls.id)).group_by(cls.role).all()
        return {role or "user": count for role, count in result}

    @classmethod
    def get_registration_stats(cls, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get registration statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        total_users = db.query(func.count(cls.id)).scalar()
        new_users = (
            db.query(func.count(cls.id)).filter(cls.created_at >= cutoff_date).scalar()
        )
        verified_users = (
            db.query(func.count(cls.id)).filter(cls.is_verified == True).scalar()
        )
        active_subscriptions = (
            db.query(func.count(cls.id))
            .filter(cls.subscription_status == "active")
            .scalar()
        )

        return {
            "total_users": total_users,
            "new_users_last_30_days": new_users,
            "verified_users": verified_users,
            "active_subscriptions": active_subscriptions,
            "verification_rate": (
                round((verified_users / total_users) * 100, 2) if total_users > 0 else 0
            ),
            "subscription_rate": (
                round((active_subscriptions / total_users) * 100, 2)
                if total_users > 0
                else 0
            ),
        }


# ==================== Event Listeners ====================


@event.listens_for(User, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Before insert event."""
    target.email = target.email.lower().strip()
    if not target.created_at:
        target.created_at = datetime.utcnow()
    if not target.updated_at:
        target.updated_at = datetime.utcnow()


@event.listens_for(User, "before_update")
def receive_before_update(mapper, connection, target):
    """Before update event."""
    target.updated_at = datetime.utcnow()


@event.listens_for(User, "after_insert")
def receive_after_insert(mapper, connection, target):
    """After insert event - could be used to create default profile/settings."""
    # This would need database session, so actual implementation
    # should be in service layer or use SQLAlchemy events with session
    pass
