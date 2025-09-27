# app/schemas/campaign.py
"""Enhanced campaign schemas matching database structure."""

from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


class CampaignCreate(BaseModel):
    """Schema for creating a campaign"""

    name: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = None
    proxy: Optional[str] = Field(None, max_length=255)
    use_captcha: Optional[bool] = True
    # Optional URLs to seed the campaign with
    urls: Optional[List[str]] = Field(default_factory=list)
    # Campaign settings
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if v:
            return v.strip()
        raise ValueError("Campaign name cannot be empty")


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = None
    proxy: Optional[str] = Field(None, max_length=255)
    use_captcha: Optional[bool] = None
    status: Optional[
        Literal["DRAFT", "RUNNING", "PAUSED", "COMPLETED", "STOPPED", "FAILED"]
    ] = None
    settings: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if v is not None:
            return v.strip()
        return v


class CampaignResponse(BaseModel):
    """Enhanced schema for campaign response matching database"""

    # Primary fields
    id: str
    user_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None

    # File information
    csv_filename: Optional[str] = None
    file_name: Optional[str] = None

    # Settings and configuration
    proxy: Optional[str] = None
    use_captcha: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

    # Statistics
    total_urls: Optional[int] = 0
    total_websites: Optional[int] = 0
    submitted_count: Optional[int] = 0
    failed_count: Optional[int] = 0
    processed: Optional[int] = 0
    successful: Optional[int] = 0
    failed: Optional[int] = 0
    email_fallback: Optional[int] = 0
    no_form: Optional[int] = 0

    # Timing and performance
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processing_duration: Optional[float] = None

    # Error tracking
    error_message: Optional[str] = None

    # Computed fields
    success_rate: Optional[float] = None
    completion_rate: Optional[float] = None

    class Config:
        from_attributes = True

    @validator("success_rate", always=True)
    def calculate_success_rate(cls, v, values):
        total = values.get("total_urls", 0) or values.get("total_websites", 0)
        successful = values.get("successful", 0)
        if total > 0:
            return round((successful / total) * 100, 2)
        return 0.0

    @validator("completion_rate", always=True)
    def calculate_completion_rate(cls, v, values):
        total = values.get("total_urls", 0) or values.get("total_websites", 0)
        processed = values.get("processed", 0)
        if total > 0:
            return round((processed / total) * 100, 2)
        return 0.0


class CampaignList(BaseModel):
    """Schema for paginated campaign list"""

    campaigns: List[CampaignResponse]
    total: int
    page: int = 1
    per_page: int = 10
    total_pages: Optional[int] = None

    @validator("total_pages", always=True)
    def calculate_total_pages(cls, v, values):
        total = values.get("total", 0)
        per_page = values.get("per_page", 10)
        if per_page > 0:
            return (total + per_page - 1) // per_page
        return 0


class CampaignStats(BaseModel):
    """Enhanced schema for campaign statistics"""

    campaign_id: str
    status: str
    total_submissions: int = 0
    completed_submissions: int = 0
    successful_submissions: int = 0
    failed_submissions: int = 0
    pending_submissions: int = 0
    progress_percent: float = 0.0
    success_rate: float = 0.0
    completion_status: Literal["not_started", "processing", "completed", "failed"] = (
        "not_started"
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None
    estimated_time_remaining: Optional[float] = None

    # Additional metrics
    captcha_encounters: int = 0
    captcha_solve_rate: float = 0.0
    email_fallback_count: int = 0
    no_form_count: int = 0
    average_retry_count: float = 0.0


class CampaignUploadRequest(BaseModel):
    """Schema for campaign CSV upload"""

    file_name: str
    proxy: Optional[str] = None
    halt_on_captcha: Optional[bool] = True
    use_captcha: Optional[bool] = True
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CampaignUploadResponse(BaseModel):
    """Schema for campaign upload response"""

    success: bool
    message: str
    campaign_id: Optional[str] = None
    job_id: Optional[str] = None
    total_urls: int = 0
    status: str = "processing"
    csv_filename: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class CampaignActionRequest(BaseModel):
    """Schema for campaign actions (start/stop/pause)"""

    action: Literal["start", "stop", "pause", "resume", "restart", "cancel"]
    reason: Optional[str] = None
    force: bool = False  # Force action even if campaign is in unexpected state


class CampaignActionResponse(BaseModel):
    """Schema for campaign action response"""

    success: bool
    message: str
    campaign_id: str
    old_status: str
    new_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    warnings: Optional[List[str]] = None


class CampaignFilter(BaseModel):
    """Schema for filtering campaigns"""

    status: Optional[
        Literal["DRAFT", "RUNNING", "PAUSED", "COMPLETED", "STOPPED", "FAILED"]
    ] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_errors: Optional[bool] = None
    min_success_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_success_rate: Optional[float] = Field(None, ge=0.0, le=100.0)


class CampaignExport(BaseModel):
    """Schema for exporting campaign data"""

    format: Literal["csv", "xlsx", "json", "pdf"] = "csv"
    include_submissions: bool = True
    include_websites: bool = True
    include_statistics: bool = True
    date_range: Optional[Dict[str, datetime]] = None


class CampaignDuplicate(BaseModel):
    """Schema for duplicating a campaign"""

    new_name: str = Field(..., min_length=1, max_length=255)
    include_urls: bool = True
    include_settings: bool = True
    auto_start: bool = False

    @validator("new_name")
    def validate_name(cls, v):
        if v:
            return v.strip()
        raise ValueError("Campaign name cannot be empty")


class CampaignBulkAction(BaseModel):
    """Schema for bulk campaign actions"""

    campaign_ids: List[str] = Field(..., min_items=1, max_items=50)
    action: Literal["start", "stop", "pause", "delete"]
    reason: Optional[str] = None

    @validator("campaign_ids")
    def validate_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate campaign IDs found")
        return v
