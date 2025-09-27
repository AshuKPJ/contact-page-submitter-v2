# File Location: C:\Ashu_Jadhav\KeepAside\CPS\contact-page-submitter\backend\app\api\__init__.py

"""
API module initialization
Import all routers here for easy access
"""

# Import routers with error handling
try:
    from .auth import router as auth_router
except ImportError as e:
    print(f"Warning: Could not import auth router: {e}")
    auth_router = None

try:
    from .analytics import router as analytics_router
except ImportError as e:
    print(f"Warning: Could not import analytics router: {e}")
    analytics_router = None

try:
    from .campaigns import router as campaigns_router
except ImportError as e:
    print(f"Warning: Could not import campaigns router: {e}")
    campaigns_router = None

try:
    from .health import router as health_router
except ImportError as e:
    print(f"Warning: Could not import health router: {e}")
    health_router = None

# These might not exist yet, so we handle them gracefully
try:
    from .submissions import router as submissions_router
except ImportError:
    submissions_router = None

try:
    from .users import router as users_router
except ImportError:
    users_router = None

try:
    from .websocket import router as websocket_router
except ImportError:
    websocket_router = None

# Export for easy access
__all__ = [
    "auth_router",
    "analytics_router",
    "campaigns_router",
    "health_router",
    "submissions_router",
    "users_router",
    "websocket_router",
]
