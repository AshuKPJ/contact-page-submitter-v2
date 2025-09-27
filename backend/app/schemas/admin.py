# app/schemas/admin.py
"""Enhanced admin schemas for system management and operations."""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid


class SystemStatus(BaseModel):
    """Enhanced system status with detailed health metrics"""

    # Basic status
    status: Literal["healthy", "degraded", "critical", "maintenance", "down"]
    environment: str = "production"
    version: str
    build_number: Optional[str] = None
    deployment_date: Optional[datetime] = None

    # Uptime metrics
    uptime: float  # in seconds
    uptime_percentage: float = 99.9
    last_restart: Optional[datetime] = None
    restart_count_24h: int = 0

    # Service statuses
    database_status: str
    api_status: str
    redis_status: Optional[str] = None
    background_worker_status: Optional[str] = None
    queue_service_status: Optional[str] = None
    captcha_service_status: Optional[str] = None
    proxy_service_status: Optional[str] = None

    # Activity metrics
    active_users: int = 0
    active_sessions: int = 0
    total_campaigns: int = 0
    active_campaigns: int = 0
    active_submissions: int = 0
    queue_depth: int = 0

    # Resource usage
    memory_usage: Optional[float] = Field(None, ge=0, le=100)
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    disk_usage: Optional[float] = Field(None, ge=0, le=100)
    network_bandwidth_usage: Optional[float] = Field(None, ge=0)
    database_connections: int = 0
    max_database_connections: int = 100

    # Performance metrics
    api_response_time_ms: float = 0.0
    database_query_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0

    # Health checks
    health_checks: Dict[str, bool] = Field(default_factory=dict)
    failed_health_checks: List[str] = Field(default_factory=list)

    # Timestamps
    last_check: datetime = Field(default_factory=datetime.utcnow)
    next_scheduled_maintenance: Optional[datetime] = None

    @validator("uptime_percentage", always=True)
    def calculate_uptime_percentage(cls, v, values):
        """Calculate uptime percentage"""
        uptime = values.get("uptime", 0)
        # Assuming 30-day period for percentage
        total_seconds_in_30_days = 30 * 24 * 3600
        if uptime > 0:
            return min(round((uptime / total_seconds_in_30_days) * 100, 2), 100)
        return 0.0

    @validator("status", always=True)
    def determine_overall_status(cls, v, values):
        """Determine overall system status based on metrics"""
        # Check critical indicators
        cpu = values.get("cpu_usage", 0)
        memory = values.get("memory_usage", 0)
        disk = values.get("disk_usage", 0)
        error_rate = values.get("error_rate", 0)
        failed_checks = len(values.get("failed_health_checks", []))

        # Critical conditions
        if (
            cpu > 95
            or memory > 95
            or disk > 95
            or error_rate > 10
            or failed_checks > 3
            or values.get("database_status") == "down"
        ):
            return "critical"

        # Degraded conditions
        elif (
            cpu > 80 or memory > 80 or disk > 80 or error_rate > 5 or failed_checks > 0
        ):
            return "degraded"

        # Maintenance mode
        elif values.get("next_scheduled_maintenance"):
            if datetime.utcnow() >= values["next_scheduled_maintenance"]:
                return "maintenance"

        # Check if explicitly down
        elif values.get("api_status") == "down":
            return "down"

        return "healthy"


class UserManagement(BaseModel):
    """Enhanced user management operations"""

    user_id: str
    action: Literal[
        "activate",
        "deactivate",
        "suspend",
        "unsuspend",
        "promote",
        "demote",
        "delete",
        "restore",
        "reset_password",
        "force_logout",
        "verify",
        "unverify",
        "lock",
        "unlock",
        "merge",
    ]

    # Action details
    reason: Optional[str] = Field(None, max_length=500)
    duration: Optional[int] = Field(
        None, description="Duration in hours for temporary actions"
    )
    new_role: Optional[Literal["user", "admin", "owner", "moderator"]] = None

    # Merge operation (for duplicate accounts)
    merge_with_user_id: Optional[str] = None

    # Notification settings
    notify_user: bool = True
    notification_message: Optional[str] = None

    # Admin metadata
    performed_by: Optional[str] = None
    requires_approval: bool = False
    approval_status: Optional[Literal["pending", "approved", "rejected"]] = None
    approved_by: Optional[str] = None

    @validator("reason")
    def validate_reason(cls, v, values):
        """Ensure reason is provided for certain actions"""
        action = values.get("action")
        critical_actions = ["delete", "suspend", "demote", "lock"]
        if action in critical_actions and not v:
            raise ValueError(f"Reason is required for action: {action}")
        if v:
            return v.strip()
        return v

    @validator("duration")
    def validate_duration(cls, v, values):
        """Validate duration for temporary actions"""
        action = values.get("action")
        temporary_actions = ["suspend", "lock"]
        if action in temporary_actions and not v:
            raise ValueError(f"Duration is required for temporary action: {action}")
        if v and v > 8760:  # Max 1 year
            raise ValueError("Duration cannot exceed 1 year (8760 hours)")
        return v


class SystemSettings(BaseModel):
    """Enhanced system settings management"""

    # Rate limiting
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)

    # Submission settings
    max_concurrent_submissions: Optional[int] = Field(None, ge=1, le=100)
    submission_delay_seconds: Optional[int] = Field(None, ge=0, le=3600)
    max_retries_per_submission: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0, le=3600)

    # System modes
    debug_mode: Optional[bool] = None
    maintenance_mode: Optional[bool] = None
    read_only_mode: Optional[bool] = None

    # Feature flags
    new_user_registration: Optional[bool] = None
    guest_access_enabled: Optional[bool] = None
    api_access_enabled: Optional[bool] = None

    # Service toggles
    captcha_service_enabled: Optional[bool] = None
    proxy_service_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    webhook_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None

    # Performance settings
    cache_enabled: Optional[bool] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=0, le=86400)
    query_timeout_seconds: Optional[int] = Field(None, ge=1, le=300)

    # Security settings
    min_password_length: Optional[int] = Field(None, ge=6, le=128)
    require_2fa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=10080)
    max_login_attempts: Optional[int] = Field(None, ge=3, le=10)
    lockout_duration_minutes: Optional[int] = Field(None, ge=5, le=1440)

    # Data retention
    log_retention_days: Optional[int] = Field(None, ge=1, le=365)
    submission_retention_days: Optional[int] = Field(None, ge=30, le=3650)
    user_data_retention_days: Optional[int] = Field(None, ge=90, le=3650)

    @model_validator(mode="after")
    def validate_settings_consistency(cls, values):
        """Ensure settings are consistent"""
        # If maintenance mode is on, certain features should be disabled
        if values.get("maintenance_mode"):
            if values.get("new_user_registration"):
                raise ValueError("Cannot enable new registrations during maintenance")

        # Rate limits should be consistent
        per_minute = values.get("rate_limit_per_minute")
        per_hour = values.get("rate_limit_per_hour")
        if per_minute and per_hour:
            if per_minute * 60 > per_hour:
                raise ValueError("Hourly rate limit is less than minute limit * 60")

        return values


class AdminAction(BaseModel):
    """Enhanced admin action logging"""

    # Action identification
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(..., max_length=255)
    action_category: Literal[
        "user_management",
        "system_config",
        "data_management",
        "security",
        "maintenance",
        "monitoring",
        "audit",
    ]

    # Target information
    target_type: Literal[
        "user",
        "campaign",
        "submission",
        "system",
        "website",
        "logs",
        "settings",
        "database",
    ]
    target_id: Optional[str] = None
    target_details: Optional[Dict[str, Any]] = None

    # Action details
    details: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

    # Execution information
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # Result
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None

    # Risk assessment
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    requires_approval: bool = False
    approval_status: Optional[Literal["pending", "approved", "rejected"]] = None

    @validator("risk_level", always=True)
    def assess_risk_level(cls, v, values):
        """Automatically assess risk level based on action"""
        action = values.get("action", "").lower()
        category = values.get("action_category")

        # Critical risk actions
        critical_actions = ["delete", "drop", "truncate", "reset", "purge"]
        if any(word in action for word in critical_actions):
            return "critical"

        # High risk categories
        if category in ["security", "system_config"]:
            return "high"

        # Medium risk
        if category in ["user_management", "data_management"]:
            return "medium"

        return "low"


class AdminResponse(BaseModel):
    """Enhanced admin operation response"""

    success: bool
    message: str

    # Response data
    data: Optional[Dict[str, Any]] = None
    affected_count: Optional[int] = None

    # Execution details
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[float] = None

    # Warnings and errors
    warnings: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Audit trail
    action_logged: bool = True
    log_id: Optional[str] = None

    # Next steps
    requires_confirmation: bool = False
    confirmation_token: Optional[str] = None
    next_actions: List[str] = Field(default_factory=list)


class SystemMetrics(BaseModel):
    """Enhanced system metrics with detailed monitoring"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Resource metrics
    cpu_usage: float = Field(0.0, ge=0, le=100)
    cpu_cores: int = 1
    memory_usage: float = Field(0.0, ge=0, le=100)
    memory_total_gb: float = 0.0
    memory_available_gb: float = 0.0
    disk_usage: float = Field(0.0, ge=0, le=100)
    disk_total_gb: float = 0.0
    disk_available_gb: float = 0.0

    # Network metrics
    network_io: Dict[str, float] = Field(
        default_factory=lambda: {
            "bytes_sent": 0.0,
            "bytes_received": 0.0,
            "packets_sent": 0,
            "packets_received": 0,
            "errors": 0,
            "dropped": 0,
        }
    )
    bandwidth_usage_mbps: float = 0.0

    # Database metrics
    database_connections: int = 0
    database_connection_pool_size: int = 0
    database_query_count: int = 0
    database_slow_queries: int = 0
    database_deadlocks: int = 0
    database_size_gb: float = 0.0

    # Application metrics
    active_sessions: int = 0
    requests_per_minute: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    response_time_avg: float = 0.0
    response_time_p50: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0

    # Queue metrics
    queue_depth: int = 0
    queue_processing_rate: float = 0.0
    queue_error_rate: float = 0.0

    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    cache_size_mb: float = 0.0

    # Custom metrics
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)

    @validator("bandwidth_usage_mbps", always=True)
    def calculate_bandwidth(cls, v, values):
        """Calculate bandwidth usage from network IO"""
        network_io = values.get("network_io", {})
        bytes_total = network_io.get("bytes_sent", 0) + network_io.get(
            "bytes_received", 0
        )
        # Convert to Mbps (assuming per second measurement)
        return round(bytes_total * 8 / 1_000_000, 2)


class UserListResponse(BaseModel):
    """Enhanced admin user list response"""

    users: List[Dict[str, Any]]

    # Pagination
    total: int
    page: int = 1
    per_page: int = 20
    total_pages: int = 1
    has_next: bool = False
    has_previous: bool = False

    # Filters applied
    filters_applied: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[Literal["asc", "desc"]] = None

    # Summary statistics
    statistics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "total_active": 0,
            "total_inactive": 0,
            "total_verified": 0,
            "total_admins": 0,
            "new_today": 0,
            "new_this_week": 0,
        }
    )

    # Query metadata
    query_time_ms: Optional[float] = None
    from_cache: bool = False

    @validator("total_pages", always=True)
    def calculate_pages(cls, v, values):
        total = values.get("total", 0)
        per_page = values.get("per_page", 20)
        if per_page > 0:
            return (total + per_page - 1) // per_page
        return 0

    @validator("has_next", always=True)
    def check_has_next(cls, v, values):
        page = values.get("page", 1)
        total_pages = values.get("total_pages", 1)
        return page < total_pages

    @validator("has_previous", always=True)
    def check_has_previous(cls, v, values):
        page = values.get("page", 1)
        return page > 1


class AdminUserFilter(BaseModel):
    """Enhanced filtering for admin user management"""

    # Status filters
    active_only: Optional[bool] = None
    inactive_only: Optional[bool] = None
    verified_only: Optional[bool] = None
    unverified_only: Optional[bool] = None

    # Role filters
    role: Optional[List[Literal["user", "admin", "owner", "moderator"]]] = None
    exclude_roles: Optional[List[str]] = None

    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None

    # Activity filters
    has_campaigns: Optional[bool] = None
    has_submissions: Optional[bool] = None
    min_campaigns: Optional[int] = Field(None, ge=0)
    min_submissions: Optional[int] = Field(None, ge=0)

    # Search
    email_search: Optional[str] = None
    name_search: Optional[str] = None
    company_search: Optional[str] = None

    # Subscription filters
    subscription_status: Optional[List[str]] = None
    subscription_tier: Optional[List[str]] = None

    # Risk filters
    suspicious_activity: Optional[bool] = None
    high_error_rate: Optional[bool] = None

    @model_validator(mode="after")
    def validate_date_ranges(cls, values):
        """Ensure date ranges are valid"""
        created_after = values.get("created_after")
        created_before = values.get("created_before")
        if created_after and created_before:
            if created_after > created_before:
                raise ValueError("created_after must be before created_before")

        last_login_after = values.get("last_login_after")
        last_login_before = values.get("last_login_before")
        if last_login_after and last_login_before:
            if last_login_after > last_login_before:
                raise ValueError("last_login_after must be before last_login_before")

        return values


class SystemLogEntry(BaseModel):
    """Enhanced system log entry"""

    id: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL"]

    # Log content
    message: str
    details: Optional[str] = None
    stack_trace: Optional[str] = None

    # Context
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    # Action information
    action: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None

    # Source information
    source: Optional[str] = None
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None

    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    http_method: Optional[str] = None
    url_path: Optional[str] = None

    # Performance
    duration_ms: Optional[float] = None

    # Tags for filtering
    tags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AuditTrail(BaseModel):
    """Enhanced audit trail entry"""

    # Core audit information
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str = Field(..., max_length=255)
    details: str = Field(..., max_length=2000)

    # Categorization
    category: Literal[
        "user_management",
        "system_config",
        "data_management",
        "security",
        "maintenance",
        "access_control",
        "compliance",
    ] = "system_config"
    severity: Literal["info", "low", "medium", "high", "critical"] = "medium"

    # Actor information
    performed_by: str
    performed_by_role: Optional[str] = None
    on_behalf_of: Optional[str] = None

    # Target information
    affected_users: List[str] = Field(default_factory=list)
    affected_resources: List[Dict[str, Any]] = Field(default_factory=list)

    # Compliance
    compliance_relevant: bool = False
    compliance_standards: List[str] = Field(default_factory=list)

    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Evidence
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    evidence_files: List[str] = Field(default_factory=list)

    @validator("action", "details")
    def strip_strings(cls, v):
        if v:
            return v.strip()
        return v

    @validator("severity", always=True)
    def assess_severity(cls, v, values):
        """Auto-assess severity based on category and action"""
        category = values.get("category")
        action = values.get("action", "").lower()

        if category == "security":
            if any(word in action for word in ["breach", "exploit", "attack"]):
                return "critical"
            return "high"
        elif category == "compliance":
            return "high"
        elif category in ["user_management", "data_management"]:
            if any(word in action for word in ["delete", "purge", "reset"]):
                return "high"
            return "medium"

        return v or "medium"


class BulkUserAction(BaseModel):
    """Enhanced bulk user actions"""

    user_ids: List[str] = Field(..., min_items=1, max_items=1000)
    action: Literal[
        "activate",
        "deactivate",
        "delete",
        "verify",
        "suspend",
        "reset_passwords",
        "send_notification",
    ]

    # Action parameters
    reason: Optional[str] = Field(None, max_length=500)
    notification_template: Optional[str] = None

    # Processing options
    batch_size: int = Field(10, ge=1, le=100)
    delay_between_batches: int = Field(1, ge=0, le=60)
    stop_on_error: bool = False
    dry_run: bool = False

    # Confirmation
    confirmation_token: Optional[str] = None
    confirmed_by: Optional[str] = None

    @validator("user_ids")
    def validate_ids(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Duplicate user IDs found")
        return v

    @validator("confirmation_token")
    def require_confirmation_for_critical(cls, v, values):
        """Require confirmation for critical actions"""
        action = values.get("action")
        critical_actions = ["delete", "reset_passwords"]
        if action in critical_actions and not v:
            raise ValueError(f"Confirmation token required for action: {action}")
        return v


class DatabaseMaintenance(BaseModel):
    """Enhanced database maintenance operations"""

    operation: Literal[
        "cleanup_logs",
        "optimize_indexes",
        "vacuum",
        "analyze",
        "backup",
        "restore",
        "migrate",
        "repair",
        "defragment",
        "reindex",
    ]

    # Target specification
    database_name: Optional[str] = None
    table_name: Optional[str] = None
    index_name: Optional[str] = None

    # Operation parameters
    days_to_keep: Optional[int] = Field(None, ge=1, le=3650)
    backup_location: Optional[str] = None
    restore_point: Optional[datetime] = None

    # Execution options
    dry_run: bool = True
    force: bool = False
    parallel_workers: int = Field(1, ge=1, le=10)

    # Scheduling
    schedule_at: Optional[datetime] = None
    recurring: bool = False
    recurrence_pattern: Optional[str] = None

    # Safety checks
    require_confirmation: bool = True
    maintenance_window_only: bool = True
    max_duration_minutes: int = Field(60, ge=1, le=480)

    @validator("backup_location")
    def validate_backup_location(cls, v, values):
        operation = values.get("operation")
        if operation in ["backup", "restore"] and not v:
            raise ValueError(f"Backup location required for operation: {operation}")
        return v


class SystemBackup(BaseModel):
    """Enhanced system backup operations"""

    backup_type: Literal[
        "full", "incremental", "differential", "tables_only", "logs_only", "config_only"
    ]

    # Backup scope
    include_user_data: bool = True
    include_logs: bool = False
    include_system_config: bool = True
    include_uploads: bool = False

    # Specific selections
    databases: Optional[List[str]] = None
    tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None

    # Backup options
    compression: bool = True
    compression_level: int = Field(6, ge=1, le=9)
    encryption: bool = False
    encryption_key_id: Optional[str] = None

    # Storage
    storage_location: Literal["local", "s3", "azure", "gcs"] = "local"
    storage_path: str
    retention_days: int = Field(30, ge=1, le=3650)

    # Verification
    verify_after_backup: bool = True
    test_restore: bool = False

    # Scheduling
    schedule_type: Optional[Literal["once", "daily", "weekly", "monthly"]] = None
    schedule_time: Optional[str] = None

    # Notifications
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    notification_emails: List[str] = Field(default_factory=list)

    @validator("encryption_key_id")
    def require_key_for_encryption(cls, v, values):
        if values.get("encryption") and not v:
            raise ValueError("Encryption key ID required when encryption is enabled")
        return v


# Export all schemas
__all__ = [
    "SystemStatus",
    "UserManagement",
    "SystemSettings",
    "AdminAction",
    "AdminResponse",
    "SystemMetrics",
    "UserListResponse",
    "AdminUserFilter",
    "SystemLogEntry",
    "AuditTrail",
    "BulkUserAction",
    "DatabaseMaintenance",
    "SystemBackup",
]
