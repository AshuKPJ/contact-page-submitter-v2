"""
Services module for Contact Page Submitter application.
"""

# Import services with proper error handling
try:
    from .auth_service import AuthService
except ImportError as e:
    print(f"Warning: Could not import AuthService: {e}")
    AuthService = None

try:
    from .campaign_service import CampaignService
except ImportError as e:
    print(f"Warning: Could not import CampaignService: {e}")
    CampaignService = None

try:
    from .captcha_service import CaptchaService
except ImportError as e:
    print(f"Warning: Could not import CaptchaService: {e}")
    CaptchaService = None

try:
    from .log_service import LogService
except ImportError as e:
    print(f"Warning: Could not import LogService: {e}")
    LogService = None

try:
    from .submission_service import SubmissionService
except ImportError as e:
    print(f"Warning: Could not import SubmissionService: {e}")
    SubmissionService = None

try:
    from .user_service import UserService
except ImportError as e:
    print(f"Warning: Could not import UserService: {e}")
    UserService = None

try:
    from .website_service import WebsiteService
except ImportError as e:
    print(f"Warning: Could not import WebsiteService: {e}")
    WebsiteService = None

try:
    from .analytics_service import AnalyticsService
except ImportError as e:
    print(f"Warning: Could not import AnalyticsService: {e}")
    AnalyticsService = None

try:
    from .admin_service import AdminService
except ImportError as e:
    print(f"Warning: Could not import AdminService: {e}")
    AdminService = None

try:
    from .csv_parser_service import CSVParserService
except ImportError as e:
    print(f"Warning: Could not import CSVParserService: {e}")
    CSVParserService = None

# Export all available services
__all__ = [
    "AuthService",
    "CampaignService",
    "CaptchaService",
    "LogService",
    "SubmissionService",
    "UserService",
    "WebsiteService",
    "AnalyticsService",
    "AdminService",
    "CSVParserService",
]
