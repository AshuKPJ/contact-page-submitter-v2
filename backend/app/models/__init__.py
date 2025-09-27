# app/models/__init__.py
"""
Database models initialization - proper import order to avoid circular dependencies.
"""

# Import Base first
from app.core.database import Base

# Import models without dependencies first
from app.models.subscription import SubscriptionPlan, Subscription
from app.models.settings import Settings
from app.models.user_profile import UserProfile

# Import logs before User (User references logs)
from app.models.logs import Log, SubmissionLog, CaptchaLog, SystemLog

# Now import User (after its dependencies)
from app.models.user import User

# Import models that depend on User
from app.models.campaign import Campaign, CampaignStatus
from app.models.website import Website
from app.models.submission import Submission, SubmissionStatus

# Export all for easy access
__all__ = [
    "Base",
    "User",
    "Campaign",
    "CampaignStatus",
    "Submission",
    "SubmissionStatus",
    "Website",
    "UserProfile",
    "SubscriptionPlan",
    "Subscription",
    "Settings",
    "Log",
    "SubmissionLog",
    "CaptchaLog",
    "SystemLog",
]
