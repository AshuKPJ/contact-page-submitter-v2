# app/core/database.py
"""Database configuration with fixed default plans creation."""

from __future__ import annotations

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import get_settings

# Setup logger
logger = logging.getLogger(__name__)

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models with naming convention
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Ensures proper cleanup after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Import all models first to register them with Base.
    """
    # Import ALL models to register them with SQLAlchemy
    try:
        import app.models
        from app.models.subscription import SubscriptionPlan, Subscription
        from app.models.settings import Settings
        from app.models.user import User
        from app.models.campaign import Campaign
        from app.models.website import Website
        from app.models.submission import Submission
        from app.models.user_profile import UserProfile
        from app.models.logs import Log, SubmissionLog, CaptchaLog, SystemLog

    except Exception as e:
        logger.warning(f"Warning during model import: {e}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized with all tables")

    # Create default subscription plans if needed
    _create_default_plans()


def _create_default_plans():
    """Create default subscription plans if they don't exist - FIXED VERSION."""
    db = SessionLocal()
    try:
        from app.models.subscription import SubscriptionPlan
        import uuid
        from decimal import Decimal

        # Check if plans exist
        existing_plans = db.query(SubscriptionPlan).count()
        logger.info(f"Found {existing_plans} existing subscription plans")

        if existing_plans == 0:
            logger.info("Creating default subscription plans...")

            # Create default plans with proper data types
            plans_data = [
                {
                    "id": uuid.uuid4(),
                    "name": "Free",
                    "description": "Basic plan for getting started",
                    "max_websites": 10,
                    "max_submissions_per_day": 50,
                    "price": Decimal("0.00"),
                    "features": {"basic_support": True, "captcha_solving": False},
                },
                {
                    "id": uuid.uuid4(),
                    "name": "Pro",
                    "description": "Professional plan for growing businesses",
                    "max_websites": 100,
                    "max_submissions_per_day": 500,
                    "price": Decimal("49.99"),
                    "features": {
                        "priority_support": True,
                        "captcha_solving": True,
                        "proxy_support": True,
                    },
                },
                {
                    "id": uuid.uuid4(),
                    "name": "Enterprise",
                    "description": "Unlimited plan for large organizations",
                    "max_websites": None,  # NULL for unlimited
                    "max_submissions_per_day": None,  # NULL for unlimited
                    "price": Decimal("199.99"),
                    "features": {
                        "dedicated_support": True,
                        "captcha_solving": True,
                        "proxy_support": True,
                        "api_access": True,
                        "custom_integrations": True,
                    },
                },
            ]

            # Create plan objects
            plans = []
            for plan_data in plans_data:
                plan = SubscriptionPlan(**plan_data)
                plans.append(plan)
                db.add(plan)

            # Commit the transaction
            db.commit()
            logger.info(
                f"✅ Successfully created {len(plans)} default subscription plans"
            )

        else:
            logger.info("Default subscription plans already exist, skipping creation")

    except Exception as e:
        logger.error(f"❌ Error creating default subscription plans: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


def test_db_connection() -> bool:
    """Test database connection."""
    try:
        db = SessionLocal()
        # Try a simple query
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_db_info() -> dict:
    """Get database connection information."""
    try:
        db = SessionLocal()
        result = db.execute("SELECT version()").fetchone()
        db.close()
        return {
            "connected": True,
            "version": result[0] if result else "Unknown",
            "url": (
                settings.DATABASE_URL.split("@")[-1]
                if "@" in settings.DATABASE_URL
                else "Hidden"
            ),
        }
    except Exception as e:
        return {"connected": False, "error": str(e), "url": "Connection failed"}
