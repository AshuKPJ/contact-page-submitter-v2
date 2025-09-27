# app/core/dependencies.py
"""Authentication and authorization dependencies"""

from typing import Optional, List
from datetime import datetime

from fastapi import Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session

# Import database and models
from app.core.database import get_db
from app.models.user import User

# Import from centralized security module
from app.core.security import verify_token, JWT_SECRET, JWT_ALGORITHM


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from JWT token"""

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Parse Bearer token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = parts[1]

        # Verify token using centralized function
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get email from token
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return user if token is present/valid; else None"""
    if not authorization:
        return None

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1]
        payload = verify_token(token)
        if not payload:
            return None

        email = payload.get("sub")
        if not email:
            return None

        return db.query(User).filter(User.email == email).first()
    except Exception:
        return None


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if user is admin or owner"""
    role = (getattr(current_user, "role", "") or "").lower()

    if role in {"admin", "owner"} or getattr(current_user, "is_superuser", False):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required",
    )


def get_admin_or_owner(current_user: User = Depends(get_current_user)) -> User:
    """Require admin or owner role"""
    role = (getattr(current_user, "role", "") or "").lower()
    if role not in {"admin", "owner"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Owner access required",
        )
    return current_user


def get_owner_only(current_user: User = Depends(get_current_user)) -> User:
    """Require owner role only"""
    role = (getattr(current_user, "role", "") or "").lower()
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required"
        )
    return current_user


def get_moderator_or_above(current_user: User = Depends(get_current_user)) -> User:
    """Require moderator, admin, or owner role"""
    role = (getattr(current_user, "role", "") or "").lower()
    if role not in {"moderator", "admin", "owner"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access or above required",
        )
    return current_user


def require_role(required_roles: List[str]):
    """Decorator to require specific roles"""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = (getattr(current_user, "role", "") or "").lower()
        if user_role not in [r.lower() for r in required_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(required_roles)}",
            )
        return current_user

    return role_checker


def has_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    role = (getattr(user, "role", "") or "").lower()

    # Admin and owner have all permissions
    if role in {"admin", "owner"}:
        return True

    # Permission mappings
    permission_map = {
        "view_users": ["admin", "owner", "moderator"],
        "edit_users": ["admin", "owner"],
        "delete_users": ["owner"],
        "view_campaigns": ["admin", "owner", "user"],
        "edit_campaigns": ["admin", "owner", "user"],
        "delete_campaigns": ["admin", "owner"],
        "view_analytics": ["admin", "owner", "user"],
        "view_own_analytics": ["admin", "owner", "user"],
        "view_logs": ["admin", "owner"],
        "manage_system": ["owner"],
    }

    allowed_roles = permission_map.get(permission, [])
    return role in allowed_roles


def require_permission(permission: str):
    """Decorator to require specific permission"""

    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user

    return permission_checker


# WebSocket authentication
async def get_current_user_ws(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """WebSocket authentication using query parameter"""
    if not token:
        return None

    try:
        payload = verify_token(token)
        if not payload:
            return None

        email = payload.get("sub")
        if not email:
            return None

        return db.query(User).filter(User.email == email).first()
    except Exception:
        return None


async def get_current_user_ws_required(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> User:
    """WebSocket authentication that requires valid user"""
    user = await get_current_user_ws(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="WebSocket authentication failed",
        )
    return user


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """Get user from JWT token"""
    payload = verify_token(token)
    if not payload:
        return None

    email = payload.get("sub")
    if not email:
        return None

    return db.query(User).filter(User.email == email).first()


def debug_token_info(authorization: Optional[str] = Header(None)) -> dict:
    """Debug token information"""
    import jwt

    if not authorization:
        return {"error": "No token provided"}

    try:
        parts = authorization.split()
        if len(parts) != 2:
            return {"error": f"Invalid format. Parts: {len(parts)}"}

        token = parts[1]

        # Decode without verification
        unverified = jwt.decode(token, options={"verify_signature": False})

        # Try with verification
        try:
            verified = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {
                "status": "valid",
                "payload": verified,
                "expires_at": (
                    datetime.fromtimestamp(verified.get("exp", 0)).isoformat()
                    if verified.get("exp")
                    else None
                ),
            }
        except jwt.ExpiredSignatureError:
            return {
                "status": "expired",
                "unverified_payload": unverified,
                "error": "Token has expired",
            }
        except jwt.InvalidTokenError as e:
            return {
                "status": "invalid",
                "unverified_payload": unverified,
                "error": str(e),
            }

    except Exception as e:
        return {"error": f"Failed to decode token: {str(e)}"}


# Export all
__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_admin_user",
    "get_admin_or_owner",
    "get_owner_only",
    "get_moderator_or_above",
    "require_role",
    "require_permission",
    "has_permission",
    "get_user_from_token",
    "get_current_user_ws",
    "get_current_user_ws_required",
    "debug_token_info",
]
