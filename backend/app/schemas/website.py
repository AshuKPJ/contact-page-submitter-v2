# app/schemas/website.py
"""Enhanced website schemas with complete database field support."""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime, timedelta
import uuid
from enum import Enum
import re
from urllib.parse import urlparse


class CaptchaDifficulty(str, Enum):
    """Captcha difficulty levels"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    IMPOSSIBLE = "impossible"


class WebsiteStatus(str, Enum):
    """Website processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    QUEUED = "queued"
    ANALYZING = "analyzing"


class FormType(str, Enum):
    """Common form types"""

    CONTACT = "contact"
    INQUIRY = "inquiry"
    QUOTE = "quote"
    SUPPORT = "support"
    FEEDBACK = "feedback"
    NEWSLETTER = "newsletter"
    REGISTRATION = "registration"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class WebsiteBase(BaseModel):
    """Base website schema"""

    campaign_id: str
    domain: str = Field(..., max_length=255)
    contact_url: Optional[str] = None

    @validator("domain")
    def validate_and_clean_domain(cls, v):
        if v:
            # Remove protocol if present
            v = re.sub(r"^https?://", "", v.lower())
            # Remove www prefix
            v = v.replace("www.", "")
            # Remove trailing slash and path
            v = v.split("/")[0]
            # Remove port if present
            v = v.split(":")[0]
            # Validate domain format
            if not re.match(r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$", v):
                raise ValueError(f"Invalid domain format: {v}")
            return v.strip()
        return v

    @validator("contact_url")
    def validate_contact_url(cls, v, values):
        if v:
            v = v.strip()
            # Add protocol if missing
            if not v.startswith(("http://", "https://")):
                v = f"https://{v}"

            # Validate URL format
            try:
                parsed = urlparse(v)
                if not parsed.netloc:
                    raise ValueError("Invalid URL format")

                # Check if URL matches the domain
                domain = values.get("domain")
                if domain:
                    url_domain = parsed.netloc.lower().replace("www.", "")
                    if not url_domain.endswith(domain):
                        # Allow subdomains
                        if not domain in url_domain:
                            raise ValueError(
                                f"Contact URL domain doesn't match website domain"
                            )
            except Exception as e:
                raise ValueError(f"Invalid contact URL: {str(e)}")

            return v
        return v


class WebsiteCreate(WebsiteBase):
    """Schema for creating a website"""

    # Optional initial analysis data
    form_detected: Optional[bool] = None
    form_type: Optional[str] = Field(None, max_length=100)
    requires_proxy: Optional[bool] = False

    # Batch creation support
    auto_detect_contact_url: bool = Field(
        True, description="Automatically detect contact URL if not provided"
    )


class WebsiteUpdate(BaseModel):
    """Enhanced schema for updating a website"""

    # Basic info
    domain: Optional[str] = Field(None, max_length=255)
    contact_url: Optional[str] = None
    status: Optional[WebsiteStatus] = None
    failure_reason: Optional[str] = None

    # Form detection results
    form_detected: Optional[bool] = None
    form_type: Optional[str] = Field(None, max_length=100)
    form_labels: Optional[List[str]] = None
    form_field_count: Optional[int] = Field(None, ge=0, le=1000)
    form_name_variants: Optional[List[str]] = None

    # Form structure (JSONB fields)
    form_field_types: Optional[Dict[str, Any]] = None
    form_field_options: Optional[Dict[str, Any]] = None
    question_answer_fields: Optional[Dict[str, Any]] = None

    # Captcha information
    has_captcha: Optional[bool] = None
    captcha_type: Optional[str] = Field(None, max_length=100)
    captcha_difficulty: Optional[CaptchaDifficulty] = None
    captcha_solution_time: Optional[int] = Field(None, ge=0, le=3600)
    captcha_metadata: Optional[Dict[str, Any]] = None

    # Proxy requirements
    requires_proxy: Optional[bool] = None
    proxy_block_type: Optional[str] = None
    last_proxy_used: Optional[str] = None

    @validator("form_field_count")
    def validate_field_count(cls, v):
        if v is not None and v < 0:
            raise ValueError("Form field count cannot be negative")
        if v is not None and v > 1000:
            raise ValueError("Form field count seems unreasonably high")
        return v

    @validator("captcha_solution_time")
    def validate_solution_time(cls, v):
        if v is not None and v < 0:
            raise ValueError("Captcha solution time cannot be negative")
        if v is not None and v > 3600:
            raise ValueError("Captcha solution time exceeds 1 hour")
        return v

    @validator("form_labels", "form_name_variants")
    def clean_string_lists(cls, v):
        if v:
            # Remove duplicates and clean strings
            cleaned = []
            seen = set()
            for item in v:
                if item and isinstance(item, str):
                    item = item.strip()
                    if item and item.lower() not in seen:
                        cleaned.append(item)
                        seen.add(item.lower())
            return cleaned if cleaned else None
        return v


class WebsiteResponse(BaseModel):
    """Enhanced schema for website response"""

    # Identifiers
    id: str
    campaign_id: Optional[str] = None
    user_id: Optional[str] = None

    # Basic information
    domain: Optional[str] = None
    contact_url: Optional[str] = None
    status: Optional[str] = None
    failure_reason: Optional[str] = None

    # Form analysis results
    form_detected: Optional[bool] = False
    form_type: Optional[str] = None
    form_labels: Optional[List[str]] = None
    form_field_count: Optional[int] = None
    form_name_variants: Optional[List[str]] = None

    # Form structure (JSONB)
    form_field_types: Optional[Dict[str, Any]] = None
    form_field_options: Optional[Dict[str, Any]] = None
    question_answer_fields: Optional[Dict[str, Any]] = None

    # Captcha information
    has_captcha: Optional[bool] = False
    captcha_type: Optional[str] = None
    captcha_difficulty: Optional[str] = None
    captcha_solution_time: Optional[int] = None
    captcha_metadata: Optional[Dict[str, Any]] = None

    # Proxy information
    requires_proxy: Optional[bool] = False
    proxy_block_type: Optional[str] = None
    last_proxy_used: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: datetime

    # Computed fields
    analysis_complete: Optional[bool] = None
    form_complexity_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    domain_reputation: Optional[str] = None

    @validator("analysis_complete", always=True)
    def check_analysis_status(cls, v, values):
        """Check if website analysis is complete"""
        status = values.get("status")
        return status in ["completed", "failed", "skipped"]

    @validator("form_complexity_score", always=True)
    def calculate_form_complexity(cls, v, values):
        """Calculate form complexity score (0-100)"""
        if not values.get("form_detected"):
            return None

        score = 0.0

        # Base score from field count
        field_count = values.get("form_field_count", 0)
        if field_count > 0:
            if field_count <= 5:
                score += 20
            elif field_count <= 10:
                score += 40
            elif field_count <= 20:
                score += 60
            else:
                score += 80

        # Add complexity for captcha
        if values.get("has_captcha"):
            difficulty = values.get("captcha_difficulty", "medium")
            difficulty_scores = {
                "easy": 5,
                "medium": 10,
                "hard": 15,
                "very_hard": 20,
                "impossible": 25,
            }
            score += difficulty_scores.get(difficulty, 10)

        # Add for proxy requirement
        if values.get("requires_proxy"):
            score += 10

        # Add for complex field types
        field_types = values.get("form_field_types", {})
        if field_types:
            complex_types = ["file", "date", "select-multiple", "radio-group"]
            complex_count = sum(1 for ft in field_types.values() if ft in complex_types)
            score += min(complex_count * 2, 10)

        return min(score, 100)

    @validator("accessibility_score", always=True)
    def calculate_accessibility(cls, v, values):
        """Calculate form accessibility score (0-100)"""
        if not values.get("form_detected"):
            return None

        score = 100.0

        # Deduct for captcha
        if values.get("has_captcha"):
            score -= 20
            difficulty = values.get("captcha_difficulty", "medium")
            if difficulty in ["hard", "very_hard", "impossible"]:
                score -= 10

        # Deduct for proxy requirement
        if values.get("requires_proxy"):
            score -= 15

        # Deduct for too many fields
        field_count = values.get("form_field_count", 0)
        if field_count > 20:
            score -= 10
        elif field_count > 30:
            score -= 20

        # Bonus for having labels
        if values.get("form_labels"):
            score += 5

        return max(score, 0)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            uuid.UUID: lambda v: str(v) if v else None,
        }


class WebsiteList(BaseModel):
    """Enhanced paginated website list"""

    websites: List[WebsiteResponse]
    total: int
    page: int = 1
    per_page: int = 10
    total_pages: Optional[int] = None

    # Additional metadata
    statistics: Optional["WebsiteStats"] = None
    filters_applied: Optional[Dict[str, Any]] = None

    @validator("total_pages", always=True)
    def calculate_pages(cls, v, values):
        total = values.get("total", 0)
        per_page = values.get("per_page", 10)
        if per_page > 0:
            return (total + per_page - 1) // per_page
        return 0


class WebsiteStats(BaseModel):
    """Enhanced website statistics"""

    # Basic counts
    total_websites: int = 0
    pending_processing: int = 0
    processing: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0

    # Form detection metrics
    with_forms_detected: int = 0
    without_forms: int = 0
    form_detection_rate: float = 0.0
    avg_form_fields: float = 0.0

    # Captcha metrics
    with_captcha: int = 0
    captcha_encounter_rate: float = 0.0
    captcha_types: Dict[str, int] = Field(default_factory=dict)
    avg_captcha_solution_time: float = 0.0

    # Proxy metrics
    requiring_proxy: int = 0
    proxy_requirement_rate: float = 0.0
    proxy_block_types: Dict[str, int] = Field(default_factory=dict)

    # Form type distribution
    form_types: Dict[str, int] = Field(default_factory=dict)

    # Performance metrics
    successfully_processed: int = 0
    failed_processing: int = 0
    success_rate: float = 0.0
    avg_processing_time: Optional[float] = None

    # Domain analysis
    unique_domains: int = 0
    top_level_domains: Dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def calculate_rates(cls, values):
        """Calculate various rate metrics"""
        total = values.get("total_websites", 0)

        if total > 0:
            # Form detection rate
            with_forms = values.get("with_forms_detected", 0)
            values["form_detection_rate"] = round((with_forms / total) * 100, 2)

            # Captcha encounter rate
            with_captcha = values.get("with_captcha", 0)
            values["captcha_encounter_rate"] = round((with_captcha / total) * 100, 2)

            # Proxy requirement rate
            requiring_proxy = values.get("requiring_proxy", 0)
            values["proxy_requirement_rate"] = round((requiring_proxy / total) * 100, 2)

            # Success rate
            successful = values.get("successfully_processed", 0)
            processed = successful + values.get("failed_processing", 0)
            if processed > 0:
                values["success_rate"] = round((successful / processed) * 100, 2)

        return values


class WebsiteFilter(BaseModel):
    """Enhanced schema for filtering websites"""

    # Campaign and user filters
    campaign_id: Optional[str] = None
    user_id: Optional[str] = None

    # Status filters
    status: Optional[WebsiteStatus] = None
    form_detected: Optional[bool] = None
    has_captcha: Optional[bool] = None
    requires_proxy: Optional[bool] = None

    # Domain filters
    domain_search: Optional[str] = None
    tld: Optional[str] = Field(
        None, description="Top-level domain filter (.com, .org, etc)"
    )

    # Date filters
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    # Form filters
    form_type: Optional[str] = None
    min_form_fields: Optional[int] = Field(None, ge=0)
    max_form_fields: Optional[int] = Field(None, ge=0)

    # Captcha filters
    captcha_type: Optional[str] = None
    captcha_difficulty: Optional[CaptchaDifficulty] = None

    # Performance filters
    max_solution_time: Optional[int] = Field(
        None, ge=0, description="Max captcha solution time in seconds"
    )

    # Sorting
    sort_by: Optional[
        Literal[
            "created_at",
            "updated_at",
            "domain",
            "form_field_count",
            "captcha_solution_time",
        ]
    ] = "created_at"
    sort_order: Optional[Literal["asc", "desc"]] = "desc"

    @validator("tld")
    def validate_tld(cls, v):
        if v:
            v = v.lower().strip()
            if not v.startswith("."):
                v = f".{v}"
            if not re.match(r"^\.[a-z]{2,}$", v):
                raise ValueError("Invalid TLD format")
            return v
        return v

    @model_validator(mode="after")
    def validate_field_range(cls, values):
        min_fields = values.get("min_form_fields")
        max_fields = values.get("max_form_fields")
        if min_fields is not None and max_fields is not None:
            if min_fields > max_fields:
                raise ValueError(
                    "min_form_fields cannot be greater than max_form_fields"
                )
        return values


class WebsiteAnalysis(BaseModel):
    """Enhanced website analysis results"""

    website_id: str
    domain: str
    analysis_status: Literal["pending", "in_progress", "completed", "failed"]

    # Form analysis
    form_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Detailed form structure and field analysis"
    )

    # Captcha analysis
    captcha_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Captcha type, difficulty, and bypass strategies"
    )

    # Contact information extraction
    contact_info: Optional[Dict[str, Any]] = Field(
        None, description="Extracted contact information from the website"
    )

    # SEO and meta information
    seo_info: Optional[Dict[str, Any]] = Field(
        None, description="SEO metadata and page information"
    )

    # Technical analysis
    technical_info: Optional[Dict[str, Any]] = Field(
        None, description="Technical details: server, CMS, technologies used"
    )

    # Security analysis
    security_info: Optional[Dict[str, Any]] = Field(
        None, description="Security headers, SSL info, WAF detection"
    )

    # Performance metrics
    analyzed_at: Optional[datetime] = None
    analysis_duration_ms: Optional[int] = None

    # Recommendations
    submission_strategy: Optional[Dict[str, Any]] = Field(
        None, description="Recommended submission strategy for this website"
    )

    # Quality scores
    data_quality_score: float = Field(0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "website_id": "web_123",
                "domain": "example.com",
                "analysis_status": "completed",
                "form_analysis": {
                    "forms_found": 2,
                    "primary_form": {
                        "type": "contact",
                        "fields": 8,
                        "required_fields": ["email", "name", "message"],
                    },
                },
                "captcha_analysis": {
                    "present": True,
                    "type": "recaptcha_v2",
                    "difficulty": "medium",
                },
                "contact_info": {
                    "email": "contact@example.com",
                    "phone": "+1-234-567-8900",
                },
                "data_quality_score": 0.85,
                "confidence_score": 0.92,
            }
        }


class WebsiteBulkUpdate(BaseModel):
    """Schema for bulk website updates"""

    website_ids: List[str] = Field(..., min_items=1, max_items=100)
    updates: WebsiteUpdate

    # Update options
    skip_completed: bool = Field(
        True, description="Skip websites already marked as completed"
    )
    update_timestamp: bool = Field(True, description="Update the updated_at timestamp")

    @validator("website_ids")
    def validate_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate website IDs found")
        return v


class WebsiteImport(BaseModel):
    """Schema for importing websites"""

    campaign_id: str
    file_type: Literal["csv", "xlsx", "txt", "json"] = "csv"

    # Column mapping
    domain_column: str = Field("domain", description="Column name for domain")
    url_column: Optional[str] = Field(
        "contact_url", description="Column name for contact URL"
    )

    # Import options
    skip_duplicates: bool = True
    validate_domains: bool = True
    auto_detect_contact_urls: bool = True
    batch_size: int = Field(100, ge=10, le=1000)

    # Additional data mapping
    column_mapping: Optional[Dict[str, str]] = Field(
        None, description="Map CSV columns to website fields"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_123",
                "file_type": "csv",
                "domain_column": "website",
                "url_column": "contact_page",
                "skip_duplicates": True,
                "validate_domains": True,
                "column_mapping": {"company": "company_name", "type": "form_type"},
            }
        }


class WebsiteExport(BaseModel):
    """Schema for exporting websites"""

    format: Literal["csv", "xlsx", "json", "xml"] = "csv"

    # Filters
    filters: Optional[WebsiteFilter] = None

    # Field selection
    fields: Optional[List[str]] = Field(
        None, description="Specific fields to export (None = all fields)"
    )

    # Export options
    include_analysis_data: bool = False
    include_form_structure: bool = False
    include_captcha_details: bool = False
    flatten_json_fields: bool = True

    # File options
    compress: bool = False
    split_large_files: bool = False
    max_rows_per_file: int = Field(10000, ge=100, le=100000)

    class Config:
        json_schema_extra = {
            "example": {
                "format": "csv",
                "include_analysis_data": True,
                "flatten_json_fields": True,
                "fields": ["domain", "contact_url", "form_detected", "has_captcha"],
            }
        }


# Export all schemas
__all__ = [
    "CaptchaDifficulty",
    "WebsiteStatus",
    "FormType",
    "WebsiteBase",
    "WebsiteCreate",
    "WebsiteUpdate",
    "WebsiteResponse",
    "WebsiteList",
    "WebsiteStats",
    "WebsiteFilter",
    "WebsiteAnalysis",
    "WebsiteBulkUpdate",
    "WebsiteImport",
    "WebsiteExport",
]
