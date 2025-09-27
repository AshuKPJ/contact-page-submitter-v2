# app/logging/core.py
"""
Core logging functionality with structured logging and multiple backends
Provides context tracking, rate limiting, and domain-specific logging methods
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from contextvars import ContextVar
from dataclasses import dataclass, asdict

from .config import LoggingConfig, LogLevel
from .formatters import StructuredFormatter, DevelopmentFormatter
from .handlers import DatabaseHandler, BufferHandler, set_buffer_handler
from .rate_limiter import RateLimiter


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
campaign_id_var: ContextVar[Optional[str]] = ContextVar("campaign_id", default=None)


@dataclass
class LogContext:
    """
    Enhanced context for log entries

    Attributes:
        request_id: Unique request identifier
        user_id: User performing the action
        campaign_id: Campaign being processed
        organization_id: Organization context
        website_id: Website being processed
        session_id: Session identifier
        correlation_id: Correlation ID for distributed tracing
        source: Source system/service
    """

    request_id: Optional[str] = None
    user_id: Optional[str] = None
    campaign_id: Optional[str] = None
    organization_id: Optional[str] = None
    website_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_context_vars(cls) -> "LogContext":
        """Create LogContext from current context variables"""
        return cls(
            request_id=request_id_var.get(),
            user_id=user_id_var.get(),
            campaign_id=campaign_id_var.get(),
        )


class AppLogger:
    """
    Enhanced application logger with structured logging and multiple backends

    Features:
    - Structured JSON logging
    - Multiple backends (console, database, buffer)
    - Rate limiting
    - Context tracking
    - Domain-specific methods
    - Performance metrics
    """

    def __init__(self, name: str, config: Optional[LoggingConfig] = None):
        """
        Initialize logger with given name and configuration

        Args:
            name: Logger name (usually __name__ of the module)
            config: Optional logging configuration, uses default if not provided
        """
        self.name = name
        self.config = config or LoggingConfig()
        self._logger = logging.getLogger(name)
        self._setup_logger()

        # Rate limiting
        if self.config.rate_limit_enabled:
            self.rate_limiter = RateLimiter(
                burst=self.config.rate_limit_burst, rate=self.config.rate_limit_rate
            )
        else:
            self.rate_limiter = None

        # Track logger metrics
        self._log_counts: Dict[str, int] = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }

    def _setup_logger(self) -> None:
        """Setup the underlying Python logger with handlers and formatters"""
        self._logger.setLevel(self.config.level.value)
        self._logger.handlers.clear()
        self._logger.propagate = False  # Don't propagate to root logger

        # Console handler
        if self.config.console_enabled:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.config.console_level.value)

            if self.config.development_mode:
                console_handler.setFormatter(DevelopmentFormatter())
            else:
                console_handler.setFormatter(StructuredFormatter())

            self._logger.addHandler(console_handler)

        # Database handler
        if self.config.database_enabled:
            try:
                db_handler = DatabaseHandler(
                    level=self.config.database_level.value,
                    batch_size=self.config.database_batch_size,
                    flush_interval=self.config.database_flush_interval,
                )
                self._logger.addHandler(db_handler)
            except Exception as e:
                print(f"Warning: Failed to setup database handler: {e}")

        # Buffer handler
        if self.config.buffer_enabled:
            buffer_handler = BufferHandler(
                buffer_size=self.config.buffer_size,
                level=self.config.buffer_level.value,
            )
            self._logger.addHandler(buffer_handler)
            # Set as global buffer handler for easy access
            set_buffer_handler(buffer_handler)

    def _should_log(self, level: str) -> bool:
        """
        Check if we should log based on rate limiting

        Args:
            level: Log level to check

        Returns:
            True if logging is allowed, False if rate limited
        """
        if not self.rate_limiter:
            return True
        return self.rate_limiter.allow(f"{self.name}:{level}")

    def _build_extra(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build extra fields for log record

        Args:
            context: Optional additional context

        Returns:
            Dictionary of extra fields for the log record
        """
        extra = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger_name": self.name,
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "campaign_id": campaign_id_var.get(),
        }

        if context:
            extra.update(context)

        # Remove None values
        return {k: v for k, v in extra.items() if v is not None}

    def _log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """
        Internal logging method with rate limiting and metrics

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            context: Optional context dictionary
            **kwargs: Additional fields to include in the log
        """
        if not self._should_log(level):
            return

        # Track metrics
        self._log_counts[level] = self._log_counts.get(level, 0) + 1

        extra = self._build_extra(context)
        extra.update(kwargs)

        try:
            self._logger.log(getattr(logging, level.upper()), message, extra=extra)
        except Exception as e:
            # Fallback to print if logging fails
            print(f"Logging failed: {e}. Message was: {message}")

    # Public API - Standard log levels
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        self._log("DEBUG", message, context, **kwargs)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        self._log("INFO", message, context, **kwargs)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        self._log("WARNING", message, context, **kwargs)

    # Alias for compatibility
    warn = warning

    def error(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        self._log("ERROR", message, context, **kwargs)

    def critical(
        self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ):
        """Log critical message"""
        self._log("CRITICAL", message, context, **kwargs)

    # Domain-specific logging methods
    def auth_event(
        self,
        action: str,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Log authentication events

        Args:
            action: Authentication action (login, logout, register, etc.)
            email: User email
            success: Whether the authentication was successful
            ip_address: Client IP address
            **kwargs: Additional context
        """
        context = {
            "event_type": "authentication",
            "action": action,
            "email": email,
            "success": success,
            "ip_address": ip_address,
        }
        context.update(kwargs)

        level = "INFO" if success else "WARNING"
        message = f"Auth {action}: {email} - {'SUCCESS' if success else 'FAILED'}"
        self._log(level, message, context)

    def campaign_event(self, action: str, campaign_id: str, **kwargs) -> None:
        """
        Log campaign-related events

        Args:
            action: Campaign action (created, started, completed, failed, etc.)
            campaign_id: Campaign identifier
            **kwargs: Additional context like total_urls, processed, etc.
        """
        context = {
            "event_type": "campaign",
            "action": action,
            "campaign_id": campaign_id,
        }
        context.update(kwargs)

        message = f"Campaign {action}: {campaign_id}"
        self.info(message, context)

    def submission_event(
        self, action: str, submission_id: str, url: str, status: str, **kwargs
    ) -> None:
        """
        Log submission events

        Args:
            action: Submission action (started, completed, failed, etc.)
            submission_id: Submission identifier
            url: Target URL
            status: Submission status
            **kwargs: Additional context like error_message, retry_count, etc.
        """
        context = {
            "event_type": "submission",
            "action": action,
            "submission_id": submission_id,
            "url": url,
            "status": status,
        }
        context.update(kwargs)

        message = f"Submission {action}: {submission_id} - {status}"
        self.info(message, context)

    def performance_metric(
        self, name: str, value: float, unit: str = "ms", **kwargs
    ) -> None:
        """
        Log performance metrics

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement (ms, seconds, bytes, etc.)
            **kwargs: Additional context
        """
        context = {
            "event_type": "metric",
            "metric_name": name,
            "metric_value": value,
            "metric_unit": unit,
        }
        context.update(kwargs)

        message = f"Metric {name}: {value}{unit}"
        self.info(message, context)

    def database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        affected_rows: int = 0,
        success: bool = True,
        **kwargs,
    ) -> None:
        """
        Log database operations

        Args:
            operation: Database operation (SELECT, INSERT, UPDATE, DELETE, etc.)
            table: Table name
            duration_ms: Operation duration in milliseconds
            affected_rows: Number of affected rows
            success: Whether the operation was successful
            **kwargs: Additional context like query details
        """
        context = {
            "event_type": "database",
            "operation": operation,
            "table": table,
            "duration_ms": duration_ms,
            "affected_rows": affected_rows,
            "success": success,
        }
        context.update(kwargs)

        level = "INFO" if success else "ERROR"
        message = (
            f"DB {operation} on {table}: {duration_ms:.2f}ms, {affected_rows} rows"
        )
        self._log(level, message, context)

    def exception(
        self,
        exc: Exception,
        handled: bool = True,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """
        Log exceptions with context

        Args:
            exc: The exception object
            handled: Whether the exception was handled
            context: Optional context dictionary
            **kwargs: Additional fields
        """
        exc_context = {
            "event_type": "exception",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "handled": handled,
        }

        if context:
            exc_context.update(context)
        exc_context.update(kwargs)

        message = f"Exception: {type(exc).__name__}: {str(exc)}"
        self.error(message, exc_context, exc_info=exc if not handled else None)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get logger metrics

        Returns:
            Dictionary containing log counts by level and other metrics
        """
        return {
            "logger_name": self.name,
            "log_counts": self._log_counts.copy(),
            "rate_limiting_enabled": self.config.rate_limit_enabled,
            "handlers": [h.__class__.__name__ for h in self._logger.handlers],
        }


# Global logger registry
_loggers: Dict[str, AppLogger] = {}
_default_config: Optional[LoggingConfig] = None


def configure_logging(config: LoggingConfig) -> None:
    """
    Configure global logging settings

    Args:
        config: Logging configuration to use as default
    """
    global _default_config
    _default_config = config

    # Also configure root logger
    logging.basicConfig(level=config.level.value, format=config.format)


def get_logger(name: str, config: Optional[LoggingConfig] = None) -> AppLogger:
    """
    Get or create a logger instance

    Args:
        name: Logger name (usually __name__ of the module)
        config: Optional specific configuration for this logger

    Returns:
        AppLogger instance
    """
    if name not in _loggers:
        effective_config = config or _default_config or LoggingConfig()
        _loggers[name] = AppLogger(name, effective_config)
    return _loggers[name]


def get_all_loggers() -> Dict[str, AppLogger]:
    """
    Get all registered loggers

    Returns:
        Dictionary of logger name to AppLogger instance
    """
    return _loggers.copy()


def reset_loggers() -> None:
    """Reset all loggers (useful for testing)"""
    global _loggers
    _loggers.clear()
