# app/schemas/user.py
"""User schemas aligned with database schema."""

from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
import re


# ==================== User Account Schemas (users table) ====================


class UserBase(BaseModel):
    """Base schema for users table fields"""

    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    profile_image_url: Optional[str] = None
    role: Optional[Literal["user", "admin", "owner", "moderator"]] = "user"
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower().strip()

    @validator("first_name", "last_name")
    def strip_strings(cls, v):
        if v:
            return v.strip()
        return v


class UserCreate(UserBase):
    """Schema for creating user account"""

    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user account"""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    profile_image_url: Optional[str] = None
    role: Optional[Literal["user", "admin", "owner", "moderator"]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

    @validator("email")
    def email_to_lower(cls, v):
        if v:
            return v.lower().strip()
        return v

    @validator("first_name", "last_name")
    def strip_strings(cls, v):
        if v:
            return v.strip()
        return v


class UserResponse(UserBase):
    """Schema for user response"""

    id: str
    plan_id: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed properties
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    is_admin: Optional[bool] = None
    is_subscribed: Optional[bool] = None
    days_since_registration: Optional[int] = None

    @validator("full_name", always=True)
    def compute_full_name(cls, v, values):
        first = values.get("first_name", "")
        last = values.get("last_name", "")
        if first and last:
            return f"{first} {last}".strip()
        return first or last or None

    @validator("display_name", always=True)
    def compute_display_name(cls, v, values):
        full_name = values.get("full_name")
        email = values.get("email", "")
        return full_name or email.split("@")[0]

    @validator("is_admin", always=True)
    def compute_is_admin(cls, v, values):
        role = values.get("role")
        return role in ["admin", "owner", "moderator"]

    @validator("days_since_registration", always=True)
    def compute_days_since_registration(cls, v, values):
        created_at = values.get("created_at")
        if created_at:
            return (datetime.utcnow() - created_at).days
        return None

    class Config:
        from_attributes = True


# ==================== User Profile Schemas (user_profiles table) ====================


class UserProfileBase(BaseModel):
    """Base schema for user_profiles table fields"""

    # Contact Information
    phone_number: Optional[str] = Field(None, max_length=50)

    # Professional Information
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    website_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=255)

    # Location Information
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)

    # Message Templates
    subject: Optional[str] = Field(None, max_length=500)
    message: Optional[str] = None

    # Business Information
    product_interest: Optional[str] = Field(None, max_length=255)
    budget_range: Optional[str] = Field(None, max_length=100)
    referral_source: Optional[str] = Field(None, max_length=255)

    # Contact Preferences
    preferred_contact: Optional[str] = Field(None, max_length=100)
    best_time_to_contact: Optional[str] = Field(None, max_length=100)
    contact_source: Optional[str] = Field(None, max_length=255)
    is_existing_customer: Optional[bool] = None

    # Language Preferences
    language: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field(None, max_length=50)

    # Additional Fields
    notes: Optional[str] = None
    form_custom_field_1: Optional[str] = Field(None, max_length=500)
    form_custom_field_2: Optional[str] = Field(None, max_length=500)
    form_custom_field_3: Optional[str] = Field(None, max_length=500)

    # DeathByCaptcha Credentials
    dbc_username: Optional[str] = Field(None, max_length=255)
    dbc_password: Optional[str] = Field(None, max_length=255)

    # Form Preferences (JSONB)
    form_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("phone_number")
    def validate_phone(cls, v):
        if v:
            # Remove common formatting characters
            cleaned = re.sub(r"[\s\-\(\)]+", "", v)
            # Check if it's a valid phone format (basic validation)
            if not re.match(r"^\+?\d{7,15}$", cleaned):
                raise ValueError("Invalid phone number format")
            return v.strip()
        return v

    @validator("website_url", "linkedin_url")
    def validate_urls(cls, v):
        if v:
            v = v.strip()
            # Add https:// if no protocol specified
            if not re.match(r"^https?://", v, re.IGNORECASE):
                v = f"https://{v}"
            # Basic URL validation
            if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", v, re.IGNORECASE):
                raise ValueError("Invalid URL format")
            # LinkedIn URL specific validation
            if "linkedin" in v.lower() and "linkedin.com" not in v.lower():
                raise ValueError("Invalid LinkedIn URL")
            return v
        return v

    @validator("zip_code")
    def validate_zip_code(cls, v):
        if v:
            v = v.strip()
            # US ZIP code validation (5 digits or 5+4 format)
            if not re.match(r"^\d{5}(-\d{4})?$", v):
                # Allow international postal codes (alphanumeric with spaces/dashes)
                if not re.match(r"^[A-Z0-9\s\-]{3,10}$", v, re.IGNORECASE):
                    raise ValueError("Invalid postal/ZIP code format")
            return v
        return v

    @validator("timezone")
    def validate_timezone(cls, v):
        if v:
            # List of common timezone formats
            valid_formats = [
                r"^[A-Z]{3,4}$",  # EST, PST, GMT
                r"^UTC[+-]\d{1,2}$",  # UTC+5, UTC-8
                r"^[A-Za-z]+/[A-Za-z_]+$",  # America/New_York
            ]
            if not any(re.match(pattern, v.strip()) for pattern in valid_formats):
                raise ValueError("Invalid timezone format")
            return v.strip()
        return v

    @validator(
        "company_name",
        "job_title",
        "city",
        "state",
        "country",
        "industry",
        "product_interest",
        "budget_range",
        "referral_source",
    )
    def strip_strings(cls, v):
        if v:
            return v.strip()
        return v


class UserProfileCreate(UserProfileBase):
    """Schema for creating user profile"""

    pass


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile - all fields optional"""

    pass


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response"""

    id: int
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed fields
    profile_completeness: Optional[float] = None
    has_contact_info: Optional[bool] = None
    has_company_info: Optional[bool] = None
    has_location_info: Optional[bool] = None
    has_dbc_credentials: Optional[bool] = None

    @validator("profile_completeness", always=True)
    def compute_completeness(cls, v, values):
        """Calculate profile completion percentage"""
        important_fields = [
            "phone_number",
            "company_name",
            "job_title",
            "city",
            "country",
            "industry",
            "preferred_contact",
            "website_url",
            "subject",
            "message",
        ]
        filled = sum(1 for field in important_fields if values.get(field))
        return round((filled / len(important_fields)) * 100, 1)

    @validator("has_contact_info", always=True)
    def compute_has_contact_info(cls, v, values):
        return bool(values.get("phone_number"))

    @validator("has_company_info", always=True)
    def compute_has_company_info(cls, v, values):
        return bool(values.get("company_name") or values.get("job_title"))

    @validator("has_location_info", always=True)
    def compute_has_location_info(cls, v, values):
        return bool(values.get("city") or values.get("state") or values.get("country"))

    @validator("has_dbc_credentials", always=True)
    def compute_has_dbc_credentials(cls, v, values):
        return bool(values.get("dbc_username") and values.get("dbc_password"))

    class Config:
        from_attributes = True


# ==================== Combined User + Profile Schemas ====================


class UserWithProfileResponse(UserResponse):
    """Schema for user with profile data"""

    profile: Optional[UserProfileResponse] = None

    class Config:
        from_attributes = True


class UserProfileFormData(BaseModel):
    """Schema for getting form data from user profile"""

    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    message: Optional[str] = None
    subject: Optional[str] = None
    industry: Optional[str] = None
    budget: Optional[str] = None
    custom_1: Optional[str] = None
    custom_2: Optional[str] = None
    custom_3: Optional[str] = None

    # Domain-specific preferences will be added dynamically


# ==================== Form Preference Schemas ====================


class FormPreferenceUpdate(BaseModel):
    """Schema for updating form preferences"""

    domain: Optional[str] = Field(
        None, description="Domain for domain-specific preferences"
    )
    preferences: Dict[str, Any] = Field(..., description="Preference key-value pairs")
    merge: bool = Field(True, description="Merge with existing preferences or replace")

    @validator("domain")
    def validate_domain(cls, v):
        if v:
            # Remove protocol and www
            v = re.sub(r"^https?://", "", v.lower())
            v = v.replace("www.", "").strip("/")
            # Basic domain validation
            if not re.match(r"^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$", v):
                raise ValueError("Invalid domain format")
            return v
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "preferences": {
                    "newsletter": "no",
                    "company_size": "10-50",
                    "budget": "Flexible",
                    "how_did_you_hear": "Search Engine",
                },
                "merge": True,
            }
        }


class FormPreferenceResponse(BaseModel):
    """Schema for form preference response"""

    global_preferences: Dict[str, Any] = Field(default_factory=dict)
    domain_preferences: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    last_updated: Optional[datetime] = None
    total_domains: int = 0

    @validator("total_domains", always=True)
    def count_domains(cls, v, values):
        return len(values.get("domain_preferences", {}))

    class Config:
        json_schema_extra = {
            "example": {
                "global_preferences": {
                    "newsletter": "no",
                    "marketing": "no",
                    "contact_me": "yes",
                },
                "domain_preferences": {
                    "example.com": {
                        "how_did_you_hear": "Other",
                        "company_size": "10-50",
                    },
                    "test.com": {"budget": "$10,000-$50,000", "timeline": "3-6 months"},
                },
                "last_updated": "2024-01-15T10:30:00Z",
                "total_domains": 2,
            }
        }


# ==================== Statistics and Analytics Schemas ====================


class UserStats(BaseModel):
    """Schema for user statistics"""

    user_id: str
    email: str

    # Campaign statistics
    total_campaigns: int = 0
    active_campaigns: int = 0
    completed_campaigns: int = 0

    # Submission statistics
    total_submissions: int = 0
    successful_submissions: int = 0
    failed_submissions: int = 0
    pending_submissions: int = 0

    # Website statistics
    total_websites: int = 0
    websites_with_forms: int = 0

    # Performance metrics
    success_rate: float = 0.0
    average_processing_time: Optional[float] = None
    captcha_solve_rate: float = 0.0

    # Activity timestamps
    last_campaign_date: Optional[datetime] = None
    last_submission_date: Optional[datetime] = None
    account_created: Optional[datetime] = None
    last_login: Optional[datetime] = None

    # Computed metrics
    account_age_days: Optional[int] = None
    activity_score: Optional[float] = None

    @validator("success_rate", always=True)
    def calculate_success_rate(cls, v, values):
        total = values.get("total_submissions", 0)
        successful = values.get("successful_submissions", 0)
        if total > 0:
            return round((successful / total) * 100, 2)
        return 0.0

    @validator("account_age_days", always=True)
    def calculate_account_age(cls, v, values):
        created = values.get("account_created")
        if created:
            return (datetime.utcnow() - created).days
        return None

    @validator("activity_score", always=True)
    def calculate_activity_score(cls, v, values):
        """Calculate activity score based on recent usage"""
        score = 0.0

        # Recent campaign activity (50% weight)
        last_campaign = values.get("last_campaign_date")
        if last_campaign:
            days_since = (datetime.utcnow() - last_campaign).days
            if days_since <= 7:
                score += 50
            elif days_since <= 30:
                score += 30
            elif days_since <= 90:
                score += 10

        # Success rate (30% weight)
        success_rate = values.get("success_rate", 0)
        score += (success_rate / 100) * 30

        # Volume (20% weight)
        total_submissions = values.get("total_submissions", 0)
        if total_submissions >= 1000:
            score += 20
        elif total_submissions >= 100:
            score += 15
        elif total_submissions >= 10:
            score += 10
        elif total_submissions > 0:
            score += 5

        return round(score, 1)


# ==================== Quick Profile Creation Schemas ====================


class UserContactProfileCreate(BaseModel):
    """Simplified schema for quick contact profile creation during registration"""

    # User table fields (required)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

    # Profile table fields (optional)
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)
    website_url: Optional[str] = Field(None, max_length=500)

    # Contact details
    subject: Optional[str] = Field(None, max_length=500)
    message: Optional[str] = None
    preferred_contact: Optional[Literal["email", "phone", "both"]] = "email"
    best_time_to_contact: Optional[str] = Field(None, max_length=100)

    # Business context
    budget_range: Optional[str] = Field(None, max_length=100)
    product_interest: Optional[str] = Field(None, max_length=255)
    referral_source: Optional[str] = Field(None, max_length=255)
    is_existing_customer: Optional[bool] = False

    # Location
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower().strip()

    @validator("first_name", "last_name", "company_name")
    def strip_and_capitalize(cls, v):
        if v:
            return v.strip().title()
        return v


# ==================== Export All Schemas ====================

__all__ = [
    # User account schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # User profile schemas
    "UserProfileBase",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResponse",
    # Combined schemas
    "UserWithProfileResponse",
    "UserProfileFormData",
    # Form preferences
    "FormPreferenceUpdate",
    "FormPreferenceResponse",
    # Statistics
    "UserStats",
    # Quick creation
    "UserContactProfileCreate",
]
