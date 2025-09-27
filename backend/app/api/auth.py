# app/api/auth.py
"""Authentication endpoints"""

from __future__ import annotations

import os
import time
import uuid
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.models.user import User

# Import everything from centralized security module
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    verify_token,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
)

# Import get_current_user from dependencies
from app.core.dependencies import get_current_user

# Initialize logger
try:
    from app.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(tags=["auth"], redirect_slashes=False)

# Security configuration
security = HTTPBearer()

# Auth configuration
ALLOW_UNVERIFIED_LOGIN = os.getenv("AUTH_ALLOW_UNVERIFIED", "true").lower() == "true"
ALLOW_INACTIVE_LOGIN = os.getenv("AUTH_ALLOW_INACTIVE", "false").lower() == "true"

# Store tokens temporarily (use Redis in production)
RESET_TOKENS = {}
VERIFICATION_TOKENS = {}


# ============ REQUEST/RESPONSE MODELS ============


class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    company_name: Optional[str] = Field(default=None, max_length=255)
    job_title: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=50)
    website_url: Optional[str] = Field(default=None, max_length=500)

    @validator("email")
    def validate_email(cls, v):
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    @validator("email")
    def validate_email(cls, v):
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime]


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class EmailVerificationRequest(BaseModel):
    email: str


# ============ UTILITY FUNCTIONS ============


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request and request.client:
        return request.client.host
    return "unknown"


# ============ AUTH ENDPOINTS ============


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest, request: Request, db: Session = Depends(get_db)
):
    """Register a new user"""
    email = payload.email.lower().strip()
    client_ip = get_client_ip(request)

    print(f"[REGISTER] Attempt from {client_ip} for email: {email}")

    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

        # Create new user
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            hashed_password=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            is_active=True,
            is_verified=False,
            role="user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(user)

        # Create user profile if additional data provided
        if any(
            [
                payload.company_name,
                payload.job_title,
                payload.phone_number,
                payload.website_url,
            ]
        ):
            try:
                db.execute(
                    text(
                        """
                        INSERT INTO user_profiles (
                            user_id, company_name, job_title, phone_number, website_url,
                            created_at, updated_at
                        ) VALUES (
                            :user_id, :company_name, :job_title, :phone_number, :website_url,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """
                    ),
                    {
                        "user_id": user_id,
                        "company_name": payload.company_name,
                        "job_title": payload.job_title,
                        "phone_number": payload.phone_number,
                        "website_url": payload.website_url,
                    },
                )
            except Exception as e:
                print(f"[REGISTER] Profile creation failed (non-critical): {e}")

        # Create default settings
        try:
            db.execute(
                text(
                    """
                    INSERT INTO settings (id, user_id, auto_submit, created_at, updated_at)
                    VALUES (gen_random_uuid(), :user_id, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                ),
                {"user_id": user_id},
            )
        except Exception as e:
            print(f"[REGISTER] Settings creation failed (non-critical): {e}")

        db.commit()

        # Generate token
        token = create_access_token(data={"sub": email, "user_id": user_id})

        print(f"[REGISTER] Success for {email}")

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": user_id,
                "email": email,
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "is_active": True,
                "is_verified": False,
                "role": "user",
            },
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"[REGISTER ERROR] {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login user"""
    try:
        email = payload.email.lower().strip()
        password = payload.password
        client_ip = get_client_ip(request)

        print(f"[LOGIN] Attempt from {client_ip} for {email}")

        # Find user
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"[LOGIN] User not found: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            print(f"[LOGIN] Invalid password for: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check account status
        if not ALLOW_INACTIVE_LOGIN and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
            )

        if not ALLOW_UNVERIFIED_LOGIN and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email to login",
            )

        # Generate token
        token = create_access_token(data={"sub": email, "user_id": str(user.id)})
        print(f"[LOGIN] Success for {email}")

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user={
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "role": user.role or "user",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[LOGIN ERROR] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user information"""
    print(f"[ME] Current user: {current_user.email}")

    # Get user profile if exists
    profile = None
    try:
        profile_result = db.execute(
            text("SELECT * FROM user_profiles WHERE user_id = :user_id"),
            {"user_id": str(current_user.id)},
        ).first()

        if profile_result:
            profile = dict(profile_result._mapping)
    except Exception as e:
        print(f"[ME] Could not fetch profile: {e}")

    # Get subscription info
    subscription = None
    try:
        if current_user.plan_id:
            plan_result = db.execute(
                text("SELECT * FROM subscription_plans WHERE id = :plan_id"),
                {"plan_id": str(current_user.plan_id)},
            ).first()

            if plan_result:
                subscription = dict(plan_result._mapping)
    except Exception as e:
        print(f"[ME] Could not fetch subscription: {e}")

    response_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role or "user",
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }

    # Add profile data if available
    if profile:
        response_data["profile"] = {
            "phone_number": profile.get("phone_number"),
            "company_name": profile.get("company_name"),
            "job_title": profile.get("job_title"),
            "website_url": profile.get("website_url"),
            "dbc_configured": bool(profile.get("dbc_username")),
        }

    # Add subscription data if available
    if subscription:
        response_data["subscription"] = {
            "plan_name": subscription.get("name", "Free"),
            "max_websites": subscription.get("max_websites", 10),
            "max_submissions_per_day": subscription.get("max_submissions_per_day", 5),
        }

    return response_data


@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    """Logout user"""
    print(f"[LOGOUT] User {current_user.email} logged out")
    return {"success": True, "message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Refresh authentication token"""
    print(f"[REFRESH] Refreshing token for {current_user.email}")

    # Generate new token
    new_token = create_access_token(
        data={"sub": current_user.email, "user_id": str(current_user.id)}
    )

    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user={
            "id": str(current_user.id),
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "role": current_user.role or "user",
        },
    )


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    print(f"[CHANGE PASSWORD] User {current_user.email} changing password")

    # Verify old password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password"
        )

    # Update password
    current_user.hashed_password = hash_password(payload.new_password)
    current_user.updated_at = datetime.utcnow()

    db.commit()

    return {"success": True, "message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)
):
    """Request password reset"""
    email = payload.email.lower().strip()
    client_ip = get_client_ip(request)

    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()

        if user:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            RESET_TOKENS[reset_token] = {
                "email": email,
                "user_id": str(user.id),
                "created_at": time.time(),
                "expires_at": time.time() + 3600,  # 1 hour
            }

            print(f"[PASSWORD RESET] Token generated for {email}: {reset_token}")

            # In production, send email here
            # send_password_reset_email(email, reset_token)

        # Always return success to prevent email enumeration
        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent.",
        }

    except Exception as e:
        print(f"[PASSWORD RESET ERROR] {e}")
        return {
            "success": True,
            "message": "If the email exists, a password reset link has been sent.",
        }


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetConfirm, request: Request, db: Session = Depends(get_db)
):
    """Reset password with token"""
    try:
        # Validate token
        if payload.token not in RESET_TOKENS:
            raise HTTPException(
                status_code=400, detail="Invalid or expired reset token"
            )

        token_data = RESET_TOKENS[payload.token]

        # Check expiration
        if time.time() > token_data["expires_at"]:
            del RESET_TOKENS[payload.token]
            raise HTTPException(status_code=400, detail="Reset token has expired")

        # Update password
        user = db.query(User).filter(User.email == token_data["email"]).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        user.hashed_password = hash_password(payload.new_password)
        user.updated_at = datetime.utcnow()
        db.commit()

        # Remove used token
        del RESET_TOKENS[payload.token]

        print(f"[PASSWORD RESET] Password reset successful for {user.email}")

        return {"success": True, "message": "Password reset successful"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[PASSWORD RESET ERROR] {e}")
        raise HTTPException(status_code=500, detail="Password reset failed")


@router.post("/verify-email")
async def verify_email(token: str, request: Request, db: Session = Depends(get_db)):
    """Verify email address"""
    try:
        # Validate token
        if token not in VERIFICATION_TOKENS:
            raise HTTPException(
                status_code=400, detail="Invalid or expired verification token"
            )

        token_data = VERIFICATION_TOKENS[token]

        # Check expiration
        if time.time() > token_data["expires_at"]:
            del VERIFICATION_TOKENS[token]
            raise HTTPException(
                status_code=400, detail="Verification token has expired"
            )

        # Update user verification status
        user = db.query(User).filter(User.email == token_data["email"]).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        user.is_verified = True
        user.updated_at = datetime.utcnow()
        db.commit()

        # Remove used token
        del VERIFICATION_TOKENS[token]

        print(f"[EMAIL VERIFICATION] Email verified for {user.email}")

        return {"success": True, "message": "Email verified successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[EMAIL VERIFICATION ERROR] {e}")
        raise HTTPException(status_code=500, detail="Email verification failed")


@router.post("/resend-verification")
async def resend_verification(
    payload: EmailVerificationRequest, request: Request, db: Session = Depends(get_db)
):
    """Resend email verification"""
    email = payload.email.lower().strip()

    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()

        if user and not user.is_verified:
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            VERIFICATION_TOKENS[verification_token] = {
                "email": email,
                "user_id": str(user.id),
                "created_at": time.time(),
                "expires_at": time.time() + 86400,  # 24 hours
            }

            print(
                f"[EMAIL VERIFICATION] Token generated for {email}: {verification_token}"
            )

            # In production, send email here
            # send_verification_email(email, verification_token)

        # Always return success
        return {
            "success": True,
            "message": "If the email exists and is unverified, a verification email has been sent.",
        }

    except Exception as e:
        print(f"[RESEND VERIFICATION ERROR] {e}")
        return {
            "success": True,
            "message": "If the email exists and is unverified, a verification email has been sent.",
        }


@router.get("/test-token")
async def test_token(authorization: Optional[str] = Header(None)):
    """Test endpoint to debug token issues"""
    import jwt

    if not authorization:
        return {"error": "No Authorization header found"}

    try:
        scheme, token = authorization.split()

        # Try to decode without verification first (for debugging)
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
        except:
            unverified = None

        # Now try with verification
        try:
            verified = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {
                "status": "valid",
                "scheme": scheme,
                "token_length": len(token),
                "payload": verified,
                "expires": (
                    datetime.fromtimestamp(verified.get("exp", 0)).isoformat()
                    if verified.get("exp")
                    else None
                ),
            }
        except jwt.ExpiredSignatureError:
            return {
                "status": "expired",
                "scheme": scheme,
                "token_length": len(token),
                "unverified_payload": unverified,
                "error": "Token has expired",
            }
        except jwt.InvalidTokenError as e:
            return {
                "status": "invalid",
                "scheme": scheme,
                "token_length": len(token),
                "unverified_payload": unverified,
                "error": str(e),
                "jwt_secret_configured": bool(
                    JWT_SECRET != "your-secret-key-change-this"
                ),
            }

    except Exception as e:
        return {
            "error": f"Failed to parse authorization header: {str(e)}",
            "header_value": (
                authorization[:50] + "..." if len(authorization) > 50 else authorization
            ),
        }


@router.get("/health")
async def health_check():
    """Auth service health check"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "allow_unverified_login": ALLOW_UNVERIFIED_LOGIN,
            "allow_inactive_login": ALLOW_INACTIVE_LOGIN,
            "jwt_algorithm": JWT_ALGORITHM,
            "jwt_expiration_hours": JWT_EXPIRATION_HOURS,
        },
    }
