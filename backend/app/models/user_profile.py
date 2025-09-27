# app/models/user_profile.py
"""UserProfile model updated to match database schema."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    Integer,
    Boolean,
    Text,
    Index,
    event,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base


class UserProfile(Base):
    """UserProfile model matching database schema."""

    __tablename__ = "user_profiles"
    __table_args__ = (
        Index("ix_user_profiles_user_id", "user_id"),
        Index("ix_user_profiles_company", "company_name"),
    )

    # Primary key (Integer as per database schema)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )

    # Contact information
    phone_number = Column(String(50), nullable=True)

    # Company information
    company_name = Column(String(255), nullable=True, index=True)
    job_title = Column(String(255), nullable=True)
    website_url = Column(String(500), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=True)

    # Location information
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)

    # Message defaults
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=True)

    # Business information
    product_interest = Column(String(255), nullable=True)
    budget_range = Column(String(100), nullable=True)
    referral_source = Column(String(255), nullable=True)

    # Contact preferences
    preferred_contact = Column(String(100), nullable=True)
    best_time_to_contact = Column(String(100), nullable=True)
    contact_source = Column(String(255), nullable=True)
    is_existing_customer = Column(Boolean, nullable=True, default=False)

    # Language preferences
    language = Column(String(50), nullable=True)
    preferred_language = Column(String(50), nullable=True)

    # Additional fields
    notes = Column(Text, nullable=True)
    form_custom_field_1 = Column(String(500), nullable=True)
    form_custom_field_2 = Column(String(500), nullable=True)
    form_custom_field_3 = Column(String(500), nullable=True)

    # DeathByCaptcha credentials
    dbc_username = Column(String(255), nullable=True)
    dbc_password = Column(String(255), nullable=True)

    # Form preferences (JSONB - learned patterns)
    form_preferences = Column(JSONB, nullable=True, default={})

    # Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="user_profile")

    def __repr__(self):
        return f"<UserProfile {self.user_id}: {self.display_name}>"

    # ==================== Validators ====================

    @validates("phone_number")
    def validate_phone(self, key, phone):
        """Validate phone number."""
        if phone:
            import re

            # Remove common formatting
            cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
            # Basic validation
            if not re.match(r"^\+?\d{7,15}$", cleaned):
                raise ValueError("Invalid phone number format")
        return phone

    @validates("website_url", "linkedin_url")
    def validate_url(self, key, url):
        """Validate URL format."""
        if url:
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            # LinkedIn specific validation
            if key == "linkedin_url" and "linkedin.com" not in url.lower():
                raise ValueError("Invalid LinkedIn URL")
        return url

    # ==================== Properties ====================

    @property
    def display_name(self) -> str:
        """Get display name."""
        if self.company_name:
            return self.company_name
        if self.user and hasattr(self.user, "full_name"):
            return self.user.full_name
        return f"Profile {self.user_id}"

    @property
    def has_contact_info(self) -> bool:
        """Check if profile has basic contact information."""
        return bool(self.phone_number or (self.user and self.user.email))

    @property
    def has_company_info(self) -> bool:
        """Check if profile has company information."""
        return bool(self.company_name or self.job_title)

    @property
    def has_location_info(self) -> bool:
        """Check if profile has location information."""
        return bool(self.city or self.state or self.country)

    @hybrid_property
    def profile_completeness(self) -> float:
        """Calculate profile completeness percentage."""
        fields = [
            self.phone_number,
            self.company_name,
            self.job_title,
            self.city,
            self.country,
            self.industry,
            self.preferred_contact,
            self.website_url,
            self.subject,
            self.message,
        ]
        filled = sum(1 for field in fields if field)
        return round((filled / len(fields)) * 100, 1)

    @property
    def location_string(self) -> str:
        """Get formatted location string."""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    @property
    def has_dbc_credentials(self) -> bool:
        """Check if DBC credentials are configured."""
        return bool(self.dbc_username and self.dbc_password)

    # ==================== Preference Management ====================

    def get_preference(
        self, key: str, domain: Optional[str] = None, default: Any = None
    ) -> Any:
        """Get a form preference value."""
        if not self.form_preferences:
            return default

        # Check domain-specific first
        if domain:
            domain = domain.lower().replace("www.", "")
            if domain in self.form_preferences:
                if key in self.form_preferences[domain]:
                    return self.form_preferences[domain][key]

        # Check global preferences
        if "global" in self.form_preferences:
            if key in self.form_preferences["global"]:
                return self.form_preferences["global"][key]

        return default

    def set_preference(
        self, key: str, value: Any, domain: Optional[str] = None
    ) -> None:
        """Set a form preference value."""
        if not self.form_preferences:
            self.form_preferences = {}

        if domain:
            domain = domain.lower().replace("www.", "")
            if domain not in self.form_preferences:
                self.form_preferences[domain] = {}
            self.form_preferences[domain][key] = value
        else:
            if "global" not in self.form_preferences:
                self.form_preferences["global"] = {}
            self.form_preferences["global"][key] = value

    def update_preferences(
        self, preferences: Dict[str, Any], domain: Optional[str] = None
    ) -> None:
        """Update multiple preferences at once."""
        for key, value in preferences.items():
            self.set_preference(key, value, domain)

    def get_domain_preferences(self, domain: str) -> Dict[str, Any]:
        """Get all preferences for a specific domain."""
        if not self.form_preferences:
            return {}

        domain = domain.lower().replace("www.", "")
        result = {}

        # Start with global preferences
        if "global" in self.form_preferences:
            result.update(self.form_preferences["global"])

        # Override with domain-specific preferences
        if domain in self.form_preferences:
            result.update(self.form_preferences[domain])

        return result

    def learn_from_submission(
        self, domain: str, field_mappings: Dict[str, Any]
    ) -> None:
        """Learn preferences from a successful submission."""
        if not domain or not field_mappings:
            return

        domain = domain.lower().replace("www.", "")

        # Common fields to learn
        learnable_fields = [
            "newsletter",
            "marketing",
            "contact_me",
            "updates",
            "how_did_you_hear",
            "budget",
            "timeline",
            "company_size",
            "industry",
            "role",
            "country",
            "state",
        ]

        for field in learnable_fields:
            # Check various field name variations
            variations = [
                field,
                field.replace("_", ""),
                field.replace("_", "-"),
                f"opt_{field}",
                f"{field}_opt",
                f"receive_{field}",
            ]

            for variation in variations:
                if variation in field_mappings:
                    self.set_preference(field, field_mappings[variation], domain)
                    break

    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences organized by domain."""
        if not self.form_preferences:
            return {"global": {}, "domains": {}}

        result = {"global": {}, "domains": {}}

        for key, value in self.form_preferences.items():
            if key == "global":
                result["global"] = value
            else:
                result["domains"][key] = value

        return result

    # ==================== Form Data Methods ====================

    def get_form_data(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get form data for auto-filling."""
        data = {
            "phone": self.phone_number,
            "company": self.company_name,
            "job_title": self.job_title,
            "website": self.website_url,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "message": self.message,
            "subject": self.subject,
            "industry": self.industry,
            "budget": self.budget_range,
        }

        # Add custom fields
        if self.form_custom_field_1:
            data["custom_1"] = self.form_custom_field_1
        if self.form_custom_field_2:
            data["custom_2"] = self.form_custom_field_2
        if self.form_custom_field_3:
            data["custom_3"] = self.form_custom_field_3

        # Merge with preferences for the domain
        if domain:
            preferences = self.get_domain_preferences(domain)
            data.update(preferences)

        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

    def merge_profile_data(self, data: Dict[str, Any]) -> None:
        """Merge data into profile (non-destructive)."""
        for key, value in data.items():
            if value and hasattr(self, key):
                current_value = getattr(self, key)
                if not current_value:
                    setattr(self, key, value)

    # ==================== Statistics Methods ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get profile statistics."""
        return {
            "profile_completeness": self.profile_completeness,
            "has_contact_info": self.has_contact_info,
            "has_company_info": self.has_company_info,
            "has_location_info": self.has_location_info,
            "has_dbc_credentials": self.has_dbc_credentials,
            "preference_count": (
                len(self.form_preferences) if self.form_preferences else 0
            ),
            "domain_count": len(
                [k for k in (self.form_preferences or {}).keys() if k != "global"]
            ),
        }

    # ==================== Serialization ====================

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        data = {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "phone_number": self.phone_number,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "website_url": self.website_url,
            "linkedin_url": self.linkedin_url,
            "industry": self.industry,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "location_string": self.location_string,
            "timezone": self.timezone,
            "preferred_contact": self.preferred_contact,
            "is_existing_customer": self.is_existing_customer,
            "profile_completeness": self.profile_completeness,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_sensitive:
            data.update(
                {
                    "subject": self.subject,
                    "message": self.message,
                    "budget_range": self.budget_range,
                    "referral_source": self.referral_source,
                    "notes": self.notes,
                    "form_preferences": self.form_preferences,
                    "has_dbc_credentials": self.has_dbc_credentials,
                }
            )

        return data

    # ==================== Class Methods ====================

    @classmethod
    def find_by_user_id(cls, db: Session, user_id: str) -> Optional["UserProfile"]:
        """Find profile by user ID."""
        return db.query(cls).filter(cls.user_id == user_id).first()

    @classmethod
    def find_incomplete(
        cls, db: Session, threshold: float = 50.0
    ) -> List["UserProfile"]:
        """Find profiles below completeness threshold."""
        # This would need a more complex query in practice
        profiles = db.query(cls).all()
        return [p for p in profiles if p.profile_completeness < threshold]


# ==================== Event Listeners ====================


@event.listens_for(UserProfile, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Before insert event."""
    if not target.created_at:
        target.created_at = datetime.utcnow()
    if not target.updated_at:
        target.updated_at = datetime.utcnow()
    if not target.form_preferences:
        target.form_preferences = {}


@event.listens_for(UserProfile, "before_update")
def receive_before_update(mapper, connection, target):
    """Before update event."""
    target.updated_at = datetime.utcnow()
