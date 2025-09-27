# app/schemas/submission.py
"""Submission schemas using Pydantic v2 syntax."""

from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime
from enum import Enum


class SubmissionStatus(str, Enum):
    """Submission status enum for schemas."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    SUCCESS = "success"  # Added for compatibility with StatusConverter
    FAILED = "failed"
    RETRY = "retry"


class ContactMethod(str, Enum):
    """Contact method enum."""

    FORM = "form"
    EMAIL = "email"
    PHONE = "phone"
    LINKEDIN = "linkedin"


class SubmissionBase(BaseModel):
    """Base submission schema."""

    url: Optional[str] = None
    status: Optional[SubmissionStatus] = SubmissionStatus.PENDING
    contact_method: Optional[ContactMethod] = ContactMethod.FORM
    success: Optional[bool] = None
    response_status: Optional[int] = None
    error_message: Optional[str] = None
    email_extracted: Optional[str] = None
    captcha_encountered: Optional[bool] = False
    captcha_solved: Optional[bool] = False
    retry_count: Optional[int] = 0

    @field_validator("response_status")
    @classmethod
    def validate_response_status(cls, v):
        if v is not None and v < 0:
            raise ValueError("Response status cannot be negative")
        return v

    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v):
        if v is not None and v < 0:
            raise ValueError("Retry count cannot be negative")
        return v


class SubmissionCreate(SubmissionBase):
    """Schema for creating submission."""

    website_id: Optional[str] = None
    campaign_id: Optional[str] = None
    form_fields_sent: Optional[Dict[str, Any]] = Field(default_factory=dict)
    field_mapping_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SubmissionUpdate(BaseModel):
    """Schema for updating submission."""

    status: Optional[SubmissionStatus] = None
    success: Optional[bool] = None
    response_status: Optional[int] = None
    error_message: Optional[str] = None
    email_extracted: Optional[str] = None
    captcha_encountered: Optional[bool] = None
    captcha_solved: Optional[bool] = None
    form_fields_sent: Optional[Dict[str, Any]] = None
    field_mapping_data: Optional[Dict[str, Any]] = None


class SubmissionResponse(SubmissionBase):
    """Schema for submission response."""

    id: str
    website_id: Optional[str] = None
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    # Computed fields
    contact_method_display: Optional[str] = None
    processing_time: Optional[float] = None
    can_retry: Optional[bool] = None
    needs_retry: Optional[bool] = None

    class Config:
        from_attributes = True


class SubmissionWithDetails(SubmissionResponse):
    """Schema for submission with sensitive details."""

    form_fields_sent: Optional[Dict[str, Any]] = None
    field_mapping_data: Optional[Dict[str, Any]] = None


class SubmissionList(BaseModel):
    """Schema for paginated list of submissions."""

    total: int
    items: List[SubmissionResponse]
    page: int = 1
    per_page: int = 50
    pages: int = 1


class FormFieldData(BaseModel):
    """Schema for form field data."""

    field_name: str = Field(..., min_length=1)
    field_value: str
    field_type: Optional[str] = "text"
    is_required: Optional[bool] = False
    field_label: Optional[str] = None


class FieldMappingData(BaseModel):
    """Schema for field mapping data - FIXED Pydantic v2 syntax."""

    # Form detection data
    form_selector: Optional[str] = None
    form_method: Optional[str] = "POST"
    form_action: Optional[str] = None

    # Field mappings
    field_mappings: Dict[str, str] = Field(default_factory=dict)
    detected_fields: List[str] = Field(default_factory=list)

    # Captcha data
    captcha_type: Optional[str] = None
    captcha_selector: Optional[str] = None
    captcha_solved: Optional[bool] = False
    captcha_solve_time: Optional[float] = None

    # Additional metadata
    form_confidence_score: Optional[float] = None
    detection_method: Optional[str] = None
    timestamp: Optional[datetime] = None

    @model_validator(mode="after")  # Pydantic v2 syntax
    def validate_form_data(self):
        """Validate form mapping data consistency."""
        # Ensure form_selector is provided if we have field mappings
        if self.field_mappings and not self.form_selector:
            raise ValueError(
                "form_selector is required when field_mappings are provided"
            )

        # Validate captcha data consistency
        if self.captcha_solved and not self.captcha_type:
            raise ValueError("captcha_type is required when captcha is solved")

        # Ensure confidence score is within valid range
        if self.form_confidence_score is not None:
            if not 0 <= self.form_confidence_score <= 1:
                raise ValueError("form_confidence_score must be between 0 and 1")

        return self

    @field_validator("form_method")
    @classmethod
    def validate_form_method(cls, v):
        if v and v.upper() not in ["GET", "POST"]:
            raise ValueError("form_method must be GET or POST")
        return v.upper() if v else v


class BulkSubmissionCreate(BaseModel):
    """Schema for creating multiple submissions."""

    campaign_id: str
    submissions: List[SubmissionCreate] = Field(..., min_items=1)

    @field_validator("submissions")
    @classmethod
    def validate_submissions(cls, v):
        if len(v) > 1000:
            raise ValueError("Cannot create more than 1000 submissions at once")
        return v


class SubmissionStats(BaseModel):
    """Schema for submission statistics."""

    total: int = 0
    pending: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    retry: int = 0
    successful: int = 0

    # Contact method breakdown
    form_submissions: int = 0
    email_fallback: int = 0
    phone_contact: int = 0
    linkedin_contact: int = 0

    # Performance metrics
    success_rate: float = 0.0
    average_processing_time: Optional[float] = None
    captcha_encounter_rate: float = 0.0
    captcha_solve_rate: float = 0.0

    @field_validator("success_rate", "captcha_encounter_rate", "captcha_solve_rate")
    @classmethod
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v


class SubmissionFilter(BaseModel):
    """Schema for filtering submissions."""

    status: Optional[List[SubmissionStatus]] = None
    contact_method: Optional[List[ContactMethod]] = None
    success: Optional[bool] = None
    captcha_encountered: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    website_id: Optional[str] = None
    campaign_id: Optional[str] = None
    limit: Optional[int] = Field(50, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)


class SubmissionRetry(BaseModel):
    """Schema for retrying submissions."""

    submission_ids: List[str] = Field(..., min_items=1, max_items=100)
    force_retry: bool = False  # Retry even if max retries reached

    @field_validator("submission_ids")
    @classmethod
    def validate_submission_ids(cls, v):
        # Basic UUID format validation
        import re

        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        for submission_id in v:
            if not uuid_pattern.match(submission_id):
                raise ValueError(f"Invalid UUID format: {submission_id}")
        return v


class SubmissionExport(BaseModel):
    """Schema for exporting submission data."""

    format: Literal["csv", "json", "xlsx"] = "csv"
    include_sensitive: bool = False
    filter: Optional[SubmissionFilter] = None
    fields: Optional[List[str]] = None  # Specific fields to export


# Export all schemas
__all__ = [
    "SubmissionStatus",
    "ContactMethod",
    "SubmissionBase",
    "SubmissionCreate",
    "SubmissionUpdate",
    "SubmissionResponse",
    "SubmissionWithDetails",
    "SubmissionList",  # Added
    "FormFieldData",
    "FieldMappingData",
    "BulkSubmissionCreate",
    "SubmissionStats",
    "SubmissionFilter",
    "SubmissionRetry",
    "SubmissionExport",
]
