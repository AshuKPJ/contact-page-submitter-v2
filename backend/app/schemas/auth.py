# app/schemas/auth.py
"""Authentication schemas aligned with database schema."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class UserLogin(BaseModel):
    """Login request schema"""

    email: EmailStr
    password: str = Field(..., min_length=1)

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower().strip()


class UserRegister(BaseModel):
    """Registration request schema aligned with users table"""

    # Required fields for users table
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

    # Optional profile fields (will be created in user_profiles table)
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)
    website_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    preferred_contact: Optional[str] = Field(None, max_length=100)

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower().strip()

    @validator("first_name", "last_name", "company_name", "job_title")
    def strip_strings(cls, v):
        if v:
            return v.strip()
        return v

    @validator("website_url", "linkedin_url")
    def validate_urls(cls, v):
        if v and not v.startswith(("http://", "https://")):
            return f"https://{v}"
        return v


class UserResponse(BaseModel):
    """User response schema matching users table structure"""

    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    role: Optional[str] = "user"
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False
    plan_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Profile data (from user_profiles table if exists)
    profile: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response schema"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: Optional[str] = None
    profile_created: Optional[bool] = False


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""

    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""

    email: EmailStr

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower().strip()


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""

    token: str
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""

    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request"""

    email: EmailStr

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower().strip()
