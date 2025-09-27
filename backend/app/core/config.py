# app/core/config.py
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, Dict, Any, List, Literal, Union
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BrowserSettings:
    """Browser configuration settings - single source of truth"""

    @property
    def headless(self) -> bool:
        """Determine if browser should run headless based on environment"""
        # DEV_AUTOMATION_HEADFUL takes precedence
        if os.getenv("DEV_AUTOMATION_HEADFUL"):
            return not (os.getenv("DEV_AUTOMATION_HEADFUL", "false").lower() == "true")
        # Fallback to BROWSER_HEADLESS
        return os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

    @property
    def slow_mo(self) -> int:
        """Get slow motion delay in milliseconds"""
        # Try DEV_AUTOMATION_SLOWMO_MS first, then BROWSER_SLOW_MO_MS
        return int(
            os.getenv("DEV_AUTOMATION_SLOWMO_MS", os.getenv("BROWSER_SLOW_MO_MS", "0"))
        )

    viewport_width: int = 1920
    viewport_height: int = 1080
    page_load_timeout: int = 30000

    @property
    def is_visible(self) -> bool:
        """Helper to check if browser will be visible"""
        return not self.headless

    def log_settings(self) -> dict:
        """Return current settings for logging"""
        return {
            "headless": self.headless,
            "visible": self.is_visible,
            "slow_mo_ms": self.slow_mo,
            "viewport": f"{self.viewport_width}x{self.viewport_height}",
            "timeout_ms": self.page_load_timeout,
        }


@dataclass
class Settings:
    """Application settings using dataclass for simplicity"""

    # Application
    APP_NAME: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "Contact Page Submitter")
    )
    VERSION: str = field(default_factory=lambda: os.getenv("APP_VERSION", "2.0.0"))
    DEBUG: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "False").lower() == "true"
    )
    PORT: int = field(default_factory=lambda: int(os.getenv("PORT", "8001")))

    # Database
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "postgresql://user:password@localhost/cps_db"
        )
    )

    # Security
    SECRET_KEY: str = field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY", "your-secret-key-change-in-production"
        )
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRATION_HOURS", "24")) * 60
    )

    # CORS
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8001",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    )

    # Browser settings - using property-based class
    browser: BrowserSettings = field(default_factory=BrowserSettings)

    # Email settings
    SMTP_HOST: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_HOST"))
    SMTP_PORT: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    SMTP_USER: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_USER"))
    SMTP_PASSWORD: Optional[str] = field(
        default_factory=lambda: os.getenv("SMTP_PASSWORD")
    )
    FROM_EMAIL: Optional[str] = field(default_factory=lambda: os.getenv("FROM_EMAIL"))

    # Captcha settings
    CAPTCHA_ENCRYPTION_KEY: str = field(
        default_factory=lambda: os.getenv(
            "CAPTCHA_ENCRYPTION_KEY", "_SS_cW5eZXsJJwQBDoczH8Ujsptjo_s0G_w6QPhnaw8="
        )
    )
    CAPTCHA_DBC_API_URL: str = field(
        default_factory=lambda: os.getenv(
            "CAPTCHA_DBC_API_URL", "http://api.dbcapi.me/api"
        )
    )
    CAPTCHA_SOLVE_TIMEOUT: int = field(
        default_factory=lambda: int(os.getenv("CAPTCHA_SOLVE_TIMEOUT", "120"))
    )

    # Worker settings
    WORKER_CONCURRENCY: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_SUBMISSIONS", "5"))
    )
    SUBMISSION_DELAY: float = field(
        default_factory=lambda: float(os.getenv("SUBMISSION_DELAY_SECONDS", "3.0"))
    )

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    )

    # Logging
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))

    # Form processing
    FORM_TIMEOUT_SECONDS: int = field(
        default_factory=lambda: int(os.getenv("FORM_TIMEOUT_SECONDS", "30"))
    )
    EMAIL_EXTRACTION_TIMEOUT: int = field(
        default_factory=lambda: int(os.getenv("EMAIL_EXTRACTION_TIMEOUT", "15"))
    )

    # Feature flags
    FEATURE_USE_BROWSER: bool = field(
        default_factory=lambda: os.getenv("FEATURE_USE_BROWSER", "true").lower()
        == "true"
    )
    FEATURE_CAPTCHA_SOLVING: bool = field(
        default_factory=lambda: os.getenv("FEATURE_CAPTCHA_SOLVING", "true").lower()
        == "true"
    )
    FEATURE_EMAIL_FALLBACK: bool = field(
        default_factory=lambda: os.getenv("FEATURE_EMAIL_FALLBACK", "true").lower()
        == "true"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()

    # Log browser configuration on first load
    import logging

    logger = logging.getLogger(__name__)
    browser_config = settings.browser.log_settings()
    logger.info(f"Browser Configuration: {browser_config}")

    return settings
