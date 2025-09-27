# app/models/settings.py
"""Settings model for user preferences and configurations."""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Text,
    Boolean,
    Index,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates, Session

from app.core.database import Base


class Settings(Base):
    """User settings and preferences model."""

    __tablename__ = "settings"
    __table_args__ = (
        Index("ix_settings_user_id", "user_id"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )

    # Settings
    default_message_template = Column(Text, nullable=True)
    captcha_api_key = Column(Text, nullable=True)
    proxy_url = Column(Text, nullable=True)
    auto_submit = Column(Boolean, nullable=True, default=False)

    # Relationships
    user = relationship("User", back_populates="settings")

    def __repr__(self):
        return f"<Settings {self.user_id}>"

    # ==================== Validators ====================

    @validates("proxy_url")
    def validate_proxy_url(self, key, url):
        """Validate proxy URL format."""
        if url:
            url = url.strip()
            if not any(url.startswith(proto) for proto in ["http://", "https://", "socks4://", "socks5://"]):
                raise ValueError("Invalid proxy URL format")
        return url

    @validates("captcha_api_key")
    def validate_captcha_key(self, key, api_key):
        """Validate captcha API key."""
        if api_key:
            api_key = api_key.strip()
            if len(api_key) < 10:
                raise ValueError("Captcha API key too short")
        return api_key

    # ==================== Properties ====================

    @property
    def has_captcha_configured(self) -> bool:
        """Check if captcha service is configured."""
        return bool(self.captcha_api_key)

    @property
    def has_proxy_configured(self) -> bool:
        """Check if proxy is configured."""
        return bool(self.proxy_url)

    @property
    def has_default_message(self) -> bool:
        """Check if default message template is set."""
        return bool(self.default_message_template)

    # ==================== Methods ====================

    def get_default_message(self, fallback: str = None) -> str:
        """Get default message template with fallback."""
        return self.default_message_template or fallback or ""

    def update_settings(self, settings_dict: Dict[str, Any]) -> None:
        """Update settings from dictionary."""
        for key, value in settings_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration for requests."""
        if not self.proxy_url:
            return None
        
        return {
            "http": self.proxy_url,
            "https": self.proxy_url
        }

    # ==================== Serialization ====================

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "auto_submit": self.auto_submit,
            "has_captcha_configured": self.has_captcha_configured,
            "has_proxy_configured": self.has_proxy_configured,
            "has_default_message": self.has_default_message,
        }

        if include_sensitive:
            data.update({
                "default_message_template": self.default_message_template,
                "captcha_api_key": self.captcha_api_key,
                "proxy_url": self.proxy_url,
            })

        return data

    # ==================== Class Methods ====================

    @classmethod
    def get_or_create(cls, db: Session, user_id: UUID) -> "Settings":
        """Get or create settings for user."""
        settings = db.query(cls).filter(cls.user_id == user_id).first()
        if not settings:
            settings = cls(user_id=user_id)
            db.add(settings)
            db.flush()
        return settings


# ==================== Event Listeners ====================


@event.listens_for(Settings, "before_insert")
def receive_before_insert(mapper, connection, target):
    """Before insert event."""
    if target.auto_submit is None:
        target.auto_submit = False