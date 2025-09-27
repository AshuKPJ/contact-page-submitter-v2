# app/schemas/analytics.py
"""Enhanced analytics schemas with comprehensive metrics and insights."""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, Dict, Any, List, Literal, Union, Tuple
from datetime import datetime, date, timedelta
from enum import Enum
import uuid


class TimeGranularity(str, Enum):
    """Time granularity for analytics aggregation"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MetricType(str, Enum):
    """Types of metrics for analytics"""

    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    RATE = "rate"
    RATIO = "ratio"


class SubmissionStats(BaseModel):
    """Enhanced submission statistics with detailed breakdowns"""

    # Core metrics
    total_submissions: int = 0
    successful_submissions: int = 0
    failed_submissions: int = 0
    pending_submissions: int = 0
    processing_submissions: int = 0
    cancelled_submissions: int = 0
    skipped_submissions: int = 0

    # Calculated rates
    success_rate: float = 0.0
    failure_rate: float = 0.0
    completion_rate: float = 0.0
    cancellation_rate: float = 0.0

    # Performance metrics
    average_processing_time: float = 0.0
    median_processing_time: float = 0.0
    min_processing_time: Optional[float] = None
    max_processing_time: Optional[float] = None
    processing_time_std_dev: Optional[float] = None

    # Retry metrics
    average_retry_count: float = 0.0
    max_retry_count: int = 0
    retry_success_rate: float = 0.0
    submissions_with_retries: int = 0

    # Captcha metrics
    captcha_encounter_rate: float = 0.0
    captcha_solve_rate: float = 0.0
    captcha_encounters: int = 0
    captcha_solved: int = 0
    captcha_failed: int = 0
    avg_captcha_solve_time: Optional[float] = None

    # Contact method breakdown
    form_submissions: int = 0
    email_submissions: int = 0
    api_submissions: int = 0
    fallback_submissions: int = 0

    # Field mapping metrics
    avg_fields_filled: float = 0.0
    avg_confidence_score: float = 0.0
    high_confidence_count: int = 0  # >80% confidence
    medium_confidence_count: int = 0  # 50-80% confidence
    low_confidence_count: int = 0  # <50% confidence

    # Time-based patterns
    peak_submission_hour: Optional[int] = None
    peak_submission_day: Optional[str] = None
    submissions_by_hour: Dict[int, int] = Field(default_factory=dict)
    submissions_by_day: Dict[str, int] = Field(default_factory=dict)

    # Error analysis
    top_error_types: List[Dict[str, Any]] = Field(default_factory=list)
    error_rate_by_hour: Dict[int, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def calculate_rates(cls, values):
        """Calculate all rate metrics"""
        total = values.get("total_submissions", 0)

        if total > 0:
            # Success/failure rates
            successful = values.get("successful_submissions", 0)
            failed = values.get("failed_submissions", 0)
            cancelled = values.get("cancelled_submissions", 0)
            completed = successful + failed

            values["success_rate"] = round((successful / total) * 100, 2)
            values["failure_rate"] = round((failed / total) * 100, 2)
            values["completion_rate"] = round((completed / total) * 100, 2)
            values["cancellation_rate"] = round((cancelled / total) * 100, 2)

            # Captcha rates
            captcha_encounters = values.get("captcha_encounters", 0)
            if captcha_encounters > 0:
                captcha_solved = values.get("captcha_solved", 0)
                values["captcha_solve_rate"] = round(
                    (captcha_solved / captcha_encounters) * 100, 2
                )
                values["captcha_encounter_rate"] = round(
                    (captcha_encounters / total) * 100, 2
                )

            # Retry success rate
            retries = values.get("submissions_with_retries", 0)
            if retries > 0:
                # Calculate based on retried submissions that eventually succeeded
                values["retry_success_rate"] = (
                    round((successful / (successful + failed)) * 100, 2)
                    if (successful + failed) > 0
                    else 0.0
                )

        return values


class CampaignAnalytics(BaseModel):
    """Enhanced campaign analytics with detailed insights"""

    # Identifiers
    campaign_id: str
    campaign_name: str
    user_id: Optional[str] = None

    # Status and timing
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Core metrics
    total_urls: int = 0
    total_websites: int = 0
    unique_domains: int = 0

    # Processing counts
    submitted_count: int = 0
    processed_count: int = 0
    successful_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
    skipped_count: int = 0

    # Special case counts
    no_form_count: int = 0
    email_fallback_count: int = 0
    captcha_blocked_count: int = 0
    proxy_required_count: int = 0

    # Calculated metrics
    success_rate: float = 0.0
    completion_rate: float = 0.0
    form_detection_rate: float = 0.0

    # Performance metrics
    average_processing_time: Optional[float] = None
    total_processing_duration: Optional[float] = None
    estimated_time_remaining: Optional[float] = None
    processing_speed: Optional[float] = None  # URLs per minute

    # Captcha analytics
    captcha_encounters: int = 0
    captcha_solve_rate: float = 0.0
    captcha_cost: Optional[float] = None

    # Domain analysis
    top_successful_domains: List[Dict[str, Any]] = Field(default_factory=list)
    top_failed_domains: List[Dict[str, Any]] = Field(default_factory=list)
    domain_success_rates: Dict[str, float] = Field(default_factory=dict)

    # Field mapping insights
    avg_fields_filled: float = 0.0
    avg_confidence_score: float = 0.0
    learned_patterns: List[str] = Field(default_factory=list)

    # Cost analysis
    estimated_cost: Optional[float] = None
    cost_per_submission: Optional[float] = None
    cost_per_success: Optional[float] = None

    # Quality metrics
    data_quality_score: float = 0.0
    campaign_efficiency_score: float = 0.0

    @model_validator(mode="after")
    def calculate_metrics(cls, values):
        """Calculate derived metrics"""
        total_urls = values.get("total_urls", 0) or values.get("total_websites", 0)

        if total_urls > 0:
            # Success rate
            successful = values.get("successful_count", 0)
            values["success_rate"] = round((successful / total_urls) * 100, 2)

            # Completion rate
            processed = values.get("processed_count", 0)
            values["completion_rate"] = round((processed / total_urls) * 100, 2)

            # Form detection rate
            forms_found = total_urls - values.get("no_form_count", 0)
            values["form_detection_rate"] = round((forms_found / total_urls) * 100, 2)

            # Processing speed
            if values.get("total_processing_duration"):
                duration_minutes = values["total_processing_duration"] / 60
                if duration_minutes > 0:
                    values["processing_speed"] = round(processed / duration_minutes, 2)

            # Cost calculations
            if values.get("estimated_cost"):
                cost = values["estimated_cost"]
                values["cost_per_submission"] = (
                    round(cost / processed, 4) if processed > 0 else 0
                )
                values["cost_per_success"] = (
                    round(cost / successful, 4) if successful > 0 else 0
                )

            # Campaign efficiency score (0-100)
            efficiency = 0.0
            efficiency += min(values["success_rate"] * 0.4, 40)  # 40% weight
            efficiency += min(values["completion_rate"] * 0.3, 30)  # 30% weight
            efficiency += min(values["form_detection_rate"] * 0.2, 20)  # 20% weight
            if values.get("avg_confidence_score", 0) > 0:
                efficiency += min(values["avg_confidence_score"] * 10, 10)  # 10% weight
            values["campaign_efficiency_score"] = round(efficiency, 1)

        return values


class UserAnalytics(BaseModel):
    """Enhanced user analytics with activity tracking"""

    # User identification
    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None

    # Account metrics
    account_created: Optional[datetime] = None
    account_age_days: int = 0
    last_login: Optional[datetime] = None
    days_since_last_login: Optional[int] = None
    is_active: bool = True
    is_verified: bool = False

    # Campaign metrics
    total_campaigns: int = 0
    active_campaigns: int = 0
    completed_campaigns: int = 0
    failed_campaigns: int = 0
    paused_campaigns: int = 0

    # Submission metrics
    total_submissions: int = 0
    successful_submissions: int = 0
    failed_submissions: int = 0
    submission_stats: SubmissionStats

    # Website metrics
    total_websites: int = 0
    unique_domains: int = 0
    websites_with_forms: int = 0

    # Performance metrics
    overall_success_rate: float = 0.0
    average_campaign_size: float = 0.0
    average_campaign_success_rate: float = 0.0
    total_processing_time: float = 0.0

    # Activity metrics
    last_campaign_date: Optional[datetime] = None
    last_submission_date: Optional[datetime] = None
    campaigns_last_30_days: int = 0
    submissions_last_30_days: int = 0
    activity_score: float = 0.0  # 0-100
    engagement_level: Literal["inactive", "low", "medium", "high", "very_high"] = (
        "inactive"
    )

    # Usage patterns
    preferred_submission_time: Optional[str] = None
    most_used_features: List[str] = Field(default_factory=list)
    average_session_duration: Optional[float] = None

    # Cost and billing
    total_spent: float = 0.0
    current_balance: float = 0.0
    subscription_tier: Optional[str] = None
    credits_remaining: Optional[int] = None

    # Quality metrics
    data_quality_score: float = 0.0
    profile_completion: float = 0.0

    @validator("account_age_days", always=True)
    def calculate_account_age(cls, v, values):
        created = values.get("account_created")
        if created:
            return (datetime.utcnow() - created).days
        return 0

    @validator("days_since_last_login", always=True)
    def calculate_days_since_login(cls, v, values):
        last_login = values.get("last_login")
        if last_login:
            return (datetime.utcnow() - last_login).days
        return None

    @validator("activity_score", always=True)
    def calculate_activity_score(cls, v, values):
        """Calculate user activity score (0-100)"""
        score = 0.0

        # Recent campaign activity (30% weight)
        campaigns_recent = values.get("campaigns_last_30_days", 0)
        if campaigns_recent >= 10:
            score += 30
        elif campaigns_recent >= 5:
            score += 20
        elif campaigns_recent >= 1:
            score += 10

        # Recent submission activity (30% weight)
        submissions_recent = values.get("submissions_last_30_days", 0)
        if submissions_recent >= 100:
            score += 30
        elif submissions_recent >= 50:
            score += 20
        elif submissions_recent >= 10:
            score += 10

        # Success rate (20% weight)
        success_rate = values.get("overall_success_rate", 0)
        score += min(success_rate * 0.2, 20)

        # Login recency (20% weight)
        days_since_login = values.get("days_since_last_login")
        if days_since_login is not None:
            if days_since_login <= 1:
                score += 20
            elif days_since_login <= 7:
                score += 15
            elif days_since_login <= 30:
                score += 10
            elif days_since_login <= 90:
                score += 5

        return round(score, 1)

    @validator("engagement_level", always=True)
    def determine_engagement_level(cls, v, values):
        """Determine user engagement level based on activity score"""
        score = values.get("activity_score", 0)
        if score >= 80:
            return "very_high"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "inactive"


class SystemAnalytics(BaseModel):
    """System-wide analytics and health metrics"""

    # System identification
    environment: str = "production"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # User metrics
    total_users: int = 0
    active_users: int = 0
    verified_users: int = 0
    new_users_today: int = 0
    new_users_this_week: int = 0
    new_users_this_month: int = 0
    user_growth_rate: float = 0.0

    # Campaign metrics
    total_campaigns: int = 0
    active_campaigns: int = 0
    running_campaigns: int = 0
    completed_campaigns: int = 0
    failed_campaigns: int = 0
    campaigns_created_today: int = 0

    # Website metrics
    total_websites: int = 0
    websites_processed_today: int = 0
    unique_domains: int = 0

    # Submission metrics
    total_submissions: int = 0
    submissions_today: int = 0
    submissions_this_hour: int = 0
    submission_stats: SubmissionStats

    # Performance metrics
    average_processing_time: float = 0.0
    system_success_rate: float = 0.0
    system_uptime_percentage: float = 99.9

    # Resource usage
    resource_usage: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_io": 0.0,
            "database_connections": 0,
        }
    )

    # Queue metrics
    queue_depth: int = 0
    processing_queue: int = 0
    retry_queue: int = 0
    failed_queue: int = 0

    # Top performing entities
    top_performing_campaigns: List[CampaignAnalytics] = Field(default_factory=list)
    most_active_users: List[Dict[str, Any]] = Field(default_factory=list)

    # Daily activity patterns
    daily_activity: Dict[str, int] = Field(default_factory=dict)
    hourly_activity: Dict[int, int] = Field(default_factory=dict)
    peak_usage_times: List[str] = Field(default_factory=list)

    # System health
    health_status: Literal["healthy", "degraded", "critical"] = "healthy"
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Financial metrics
    revenue_today: float = 0.0
    revenue_this_month: float = 0.0
    average_revenue_per_user: float = 0.0

    @validator("health_status", always=True)
    def determine_health_status(cls, v, values):
        """Determine system health based on metrics"""
        # Check various health indicators
        cpu_usage = values.get("resource_usage", {}).get("cpu_usage", 0)
        memory_usage = values.get("resource_usage", {}).get("memory_usage", 0)
        queue_depth = values.get("queue_depth", 0)
        active_alerts = len(values.get("active_alerts", []))

        if cpu_usage > 90 or memory_usage > 90 or active_alerts > 5:
            return "critical"
        elif (
            cpu_usage > 70
            or memory_usage > 70
            or queue_depth > 1000
            or active_alerts > 0
        ):
            return "degraded"
        else:
            return "healthy"


class TimeSeriesData(BaseModel):
    """Time series data point for analytics charts"""

    timestamp: Union[datetime, date, str]
    value: Union[int, float]
    label: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("timestamp")
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return datetime.strptime(v, "%Y-%m-%d")
        return v


class DailyStats(BaseModel):
    """Daily statistics with time series data"""

    date_range: Tuple[datetime, datetime]
    days: int = 30
    series: List[TimeSeriesData] = Field(default_factory=list)

    # Summary statistics
    total: int = 0
    average: float = 0.0
    median: float = 0.0
    min: float = 0.0
    max: float = 0.0
    std_dev: float = 0.0

    # Trend analysis
    trend: Literal["increasing", "decreasing", "stable"] = "stable"
    trend_percentage: float = 0.0

    # Comparisons
    vs_previous_period: float = 0.0
    vs_same_period_last_month: Optional[float] = None

    @model_validator(mode="after")
    def calculate_statistics(cls, values):
        """Calculate summary statistics from series data"""
        series = values.get("series", [])
        if series:
            data_values = [point.value for point in series]
            values["total"] = sum(data_values)
            values["average"] = sum(data_values) / len(data_values)
            values["min"] = min(data_values)
            values["max"] = max(data_values)

            # Calculate trend
            if len(data_values) >= 7:
                first_week_avg = sum(data_values[:7]) / 7
                last_week_avg = sum(data_values[-7:]) / 7
                if last_week_avg > first_week_avg * 1.1:
                    values["trend"] = "increasing"
                    values["trend_percentage"] = (
                        (last_week_avg - first_week_avg) / first_week_avg
                    ) * 100
                elif last_week_avg < first_week_avg * 0.9:
                    values["trend"] = "decreasing"
                    values["trend_percentage"] = (
                        (first_week_avg - last_week_avg) / first_week_avg
                    ) * -100
                else:
                    values["trend"] = "stable"

        return values


class PerformanceAnalytics(BaseModel):
    """Performance analytics for campaigns and submissions"""

    time_period: Tuple[datetime, datetime]

    # Campaign performance
    campaigns: List[CampaignAnalytics] = Field(default_factory=list)
    campaign_comparison: Optional[Dict[str, Any]] = None

    # Domain performance
    domain_statistics: List[Dict[str, Any]] = Field(default_factory=list)
    domain_success_rates: Dict[str, float] = Field(default_factory=dict)
    problematic_domains: List[str] = Field(default_factory=list)

    # Performance metrics
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Trends
    trends: Dict[str, List[TimeSeriesData]] = Field(default_factory=dict)

    # Benchmarks
    benchmarks: Dict[str, float] = Field(
        default_factory=lambda: {
            "target_success_rate": 80.0,
            "target_processing_time": 5.0,
            "target_captcha_solve_rate": 90.0,
            "target_form_detection_rate": 95.0,
        }
    )

    # Performance scores
    overall_performance_score: float = 0.0
    efficiency_score: float = 0.0
    quality_score: float = 0.0
    speed_score: float = 0.0

    @model_validator(mode="after")
    def calculate_performance_scores(cls, values):
        """Calculate overall performance scores"""
        metrics = values.get("metrics", {})
        benchmarks = values.get("benchmarks", {})

        # Calculate individual scores based on benchmarks
        scores = []

        # Success rate score
        if "success_rate" in metrics:
            target = benchmarks.get("target_success_rate", 80)
            actual = metrics["success_rate"]
            scores.append(min(actual / target * 100, 100))

        # Processing time score (inverse - lower is better)
        if "avg_processing_time" in metrics:
            target = benchmarks.get("target_processing_time", 5)
            actual = metrics["avg_processing_time"]
            if actual > 0:
                scores.append(min(target / actual * 100, 100))

        # Calculate overall score
        if scores:
            values["overall_performance_score"] = round(sum(scores) / len(scores), 1)

        return values


class AnalyticsFilter(BaseModel):
    """Comprehensive filter for analytics queries"""

    # Time filters
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    time_granularity: Optional[TimeGranularity] = TimeGranularity.DAILY

    # Entity filters
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    website_id: Optional[str] = None

    # Status filters
    status: Optional[List[str]] = None
    include_inactive: bool = False

    # Grouping
    group_by: Optional[
        List[
            Literal[
                "day", "week", "month", "hour", "campaign", "user", "domain", "status"
            ]
        ]
    ] = None

    # Limits
    limit: Optional[int] = Field(None, ge=1, le=10000)
    offset: Optional[int] = Field(None, ge=0)

    # Metrics selection
    metrics: Optional[List[str]] = None
    include_detailed_breakdown: bool = False

    @model_validator(mode="after")
    def validate_date_range(cls, values):
        date_from = values.get("date_from")
        date_to = values.get("date_to")

        if date_from and date_to:
            if date_from > date_to:
                raise ValueError("date_from must be before date_to")

            # Limit range to 1 year for performance
            if (date_to - date_from).days > 365:
                raise ValueError("Date range cannot exceed 365 days")

        return values


class CampaignComparisonAnalytics(BaseModel):
    """Compare multiple campaigns"""

    campaigns: List[CampaignAnalytics]

    # Comparison metrics
    comparison_metrics: Dict[str, Any] = Field(default_factory=dict)

    # Rankings
    best_performing: Optional[CampaignAnalytics] = None
    worst_performing: Optional[CampaignAnalytics] = None
    most_efficient: Optional[CampaignAnalytics] = None

    # Averages across campaigns
    average_metrics: Dict[str, float] = Field(default_factory=dict)

    # Statistical analysis
    variance_metrics: Dict[str, float] = Field(default_factory=dict)
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None

    @model_validator(mode="after")
    def analyze_campaigns(cls, values):
        """Analyze and compare campaigns"""
        campaigns = values.get("campaigns", [])

        if len(campaigns) >= 2:
            # Find best and worst performing
            sorted_by_success = sorted(
                campaigns, key=lambda x: x.success_rate, reverse=True
            )
            values["best_performing"] = sorted_by_success[0]
            values["worst_performing"] = sorted_by_success[-1]

            # Find most efficient
            sorted_by_efficiency = sorted(
                campaigns, key=lambda x: x.campaign_efficiency_score, reverse=True
            )
            values["most_efficient"] = sorted_by_efficiency[0]

            # Calculate averages
            avg_success_rate = sum(c.success_rate for c in campaigns) / len(campaigns)
            avg_completion_rate = sum(c.completion_rate for c in campaigns) / len(
                campaigns
            )
            avg_processing_time = sum(
                c.average_processing_time or 0 for c in campaigns
            ) / len(campaigns)

            values["average_metrics"] = {
                "avg_success_rate": round(avg_success_rate, 2),
                "avg_completion_rate": round(avg_completion_rate, 2),
                "avg_processing_time": round(avg_processing_time, 2),
            }

        return values


class DomainAnalytics(BaseModel):
    """Domain-specific analytics"""

    domain: str

    # Attempt metrics
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    pending_attempts: int = 0

    # Calculated rates
    success_rate: float = 0.0
    failure_rate: float = 0.0

    # Performance metrics
    average_processing_time: float = 0.0
    average_retry_count: float = 0.0

    # Form analysis
    form_detection_rate: float = 0.0
    avg_form_fields: float = 0.0
    common_form_types: List[str] = Field(default_factory=list)

    # Captcha metrics
    captcha_encounter_rate: float = 0.0
    captcha_types_encountered: List[str] = Field(default_factory=list)

    # Proxy requirements
    proxy_required: bool = False
    proxy_success_rate: float = 0.0

    # Timing
    last_attempt: Optional[datetime] = None
    first_attempt: Optional[datetime] = None

    # Failure analysis
    common_failure_reasons: List[Dict[str, Any]] = Field(default_factory=list)
    error_patterns: Dict[str, int] = Field(default_factory=dict)

    # Recommendations
    recommended_strategy: Optional[str] = None
    confidence_level: Literal["high", "medium", "low"] = "medium"

    @model_validator(mode="after")
    def calculate_domain_metrics(cls, values):
        """Calculate domain-specific metrics"""
        total = values.get("total_attempts", 0)

        if total > 0:
            successful = values.get("successful_attempts", 0)
            failed = values.get("failed_attempts", 0)

            values["success_rate"] = round((successful / total) * 100, 2)
            values["failure_rate"] = round((failed / total) * 100, 2)

            # Determine confidence level
            if total >= 100 and values["success_rate"] > 80:
                values["confidence_level"] = "high"
            elif total >= 50 or values["success_rate"] > 60:
                values["confidence_level"] = "medium"
            else:
                values["confidence_level"] = "low"

            # Recommend strategy
            if values["success_rate"] > 80:
                values["recommended_strategy"] = "Standard submission"
            elif values["captcha_encounter_rate"] > 50:
                values["recommended_strategy"] = "Use advanced captcha solving"
            elif values.get("proxy_required"):
                values["recommended_strategy"] = "Use rotating proxies"
            else:
                values["recommended_strategy"] = "Manual review recommended"

        return values


class RealtimeAnalytics(BaseModel):
    """Real-time system analytics"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Current activity
    active_campaigns: int = 0
    active_users: int = 0
    submissions_in_progress: int = 0

    # Last hour metrics
    submissions_last_hour: int = 0
    success_rate_last_hour: float = 0.0
    errors_last_hour: int = 0
    new_users_last_hour: int = 0

    # Queue status
    queue_depth: int = 0
    avg_queue_wait_time: float = 0.0

    # System load
    system_load: Dict[str, float] = Field(
        default_factory=lambda: {
            "cpu": 0.0,
            "memory": 0.0,
            "disk_io": 0.0,
            "network": 0.0,
        }
    )

    # Performance
    avg_response_time_ms: float = 0.0
    requests_per_second: float = 0.0

    # Alerts
    active_alerts: List[Dict[str, Any]] = Field(default_factory=list)

    # Predictions
    predicted_completions_next_hour: Optional[int] = None
    predicted_load_next_hour: Optional[str] = None


class AnalyticsExport(BaseModel):
    """Export configuration for analytics data"""

    export_type: Literal["summary", "detailed", "raw_data", "charts", "report"]
    format: Literal["csv", "xlsx", "json", "pdf", "html"] = "csv"

    # Filters
    date_range: Optional[Tuple[datetime, datetime]] = None
    filters: Optional[AnalyticsFilter] = None

    # Content selection
    include_charts: bool = False
    include_raw_data: bool = False
    include_summary: bool = True
    include_recommendations: bool = False

    # Grouping and aggregation
    group_by: Optional[List[str]] = None
    aggregation: Optional[MetricType] = MetricType.SUM

    # Export options
    compress: bool = False
    split_large_files: bool = False
    max_rows: int = Field(100000, ge=100, le=1000000)

    # Delivery
    email_to: Optional[str] = None
    webhook_url: Optional[str] = None


# Export all schemas
__all__ = [
    "TimeGranularity",
    "MetricType",
    "SubmissionStats",
    "CampaignAnalytics",
    "UserAnalytics",
    "SystemAnalytics",
    "TimeSeriesData",
    "DailyStats",
    "PerformanceAnalytics",
    "AnalyticsFilter",
    "CampaignComparisonAnalytics",
    "DomainAnalytics",
    "RealtimeAnalytics",
    "AnalyticsExport",
]
