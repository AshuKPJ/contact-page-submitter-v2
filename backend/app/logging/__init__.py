# app/logging/__init__.py
"""
Enhanced logging module for CPS (Contact Page Submitter)
Provides structured logging with multiple backends and real-time streaming

Key Features:
- Structured JSON logging for production
- Human-readable logging for development
- Multiple backends (console, database, buffer)
- Real-time log streaming
- Rate limiting
- Context tracking (request_id, user_id, campaign_id)
"""

from .config import LoggingConfig, LogLevel
from .core import (
    AppLogger,
    get_logger,
    configure_logging,
    request_id_var,
    user_id_var,
    campaign_id_var,
    LogContext,
)
from .decorators import log_function, log_exceptions, log_performance
from .formatters import StructuredFormatter, DevelopmentFormatter
from .handlers import (
    DatabaseHandler,
    BufferHandler,
    get_buffer_handler,
    set_buffer_handler,
)
from .middleware import LoggingMiddleware
from .rate_limiter import RateLimiter

# Version info
__version__ = "2.0.0"
__author__ = "CPS Team"

# Convenience imports for backward compatibility
from .core import get_logger as getLogger
from .decorators import log_function as logFunction
from .decorators import log_exceptions as logExceptions

__all__ = [
    # Configuration
    "LoggingConfig",
    "LogLevel",
    "configure_logging",
    # Core
    "AppLogger",
    "get_logger",
    "getLogger",  # Alias
    "LogContext",
    # Context variables
    "request_id_var",
    "user_id_var",
    "campaign_id_var",
    # Decorators
    "log_function",
    "log_exceptions",
    "log_performance",
    "logFunction",  # Alias
    "logExceptions",  # Alias
    # Formatters
    "StructuredFormatter",
    "DevelopmentFormatter",
    # Handlers
    "DatabaseHandler",
    "BufferHandler",
    "get_buffer_handler",
    "set_buffer_handler",
    # Middleware
    "LoggingMiddleware",
    # Rate limiting
    "RateLimiter",
]

# Initialize default configuration from environment
import os

default_config = LoggingConfig()
if os.getenv("LOG_AUTO_CONFIGURE", "true").lower() == "true":
    configure_logging(default_config)
