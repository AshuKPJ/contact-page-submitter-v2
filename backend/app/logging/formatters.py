# app/logging/formatters.py
"""
Custom formatters for structured logging
Provides JSON formatting for production and human-readable formatting for development
"""
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """
    Formatter that outputs structured JSON logs
    Ideal for production environments and log aggregation systems
    """

    def __init__(self, include_extra: bool = True):
        """
        Initialize the structured formatter

        Args:
            include_extra: Whether to include extra fields from LogRecord
        """
        super().__init__()
        self.include_extra = include_extra

        # Standard fields to exclude from extra
        self.standard_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "exc_info",
            "exc_text",
            "stack_info",
            "getMessage",
            "message",
        }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON

        Args:
            record: LogRecord to format

        Returns:
            JSON string representation of the log
        """
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields from record if requested
        if self.include_extra and hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in log_data and not key.startswith("_"):
                    # Skip standard logging fields
                    if key not in self.standard_fields:
                        try:
                            # Try to serialize the value
                            json.dumps(value, default=str)
                            log_data[key] = value
                        except (TypeError, ValueError):
                            # If serialization fails, convert to string
                            log_data[key] = str(value)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exception_type"] = (
                record.exc_info[0].__name__ if record.exc_info[0] else None
            )

        # Add stack info if present
        if record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)

        try:
            return json.dumps(log_data, default=str, separators=(",", ":"))
        except Exception as e:
            # Fallback if JSON serialization fails
            fallback = {
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "logger": "formatter",
                "message": f"Failed to format log: {str(e)}",
                "original_message": str(record.getMessage())[:1000],
            }
            return json.dumps(fallback)


class DevelopmentFormatter(logging.Formatter):
    """
    Human-readable formatter for development
    Includes color coding and context information
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True, include_context: bool = True):
        """
        Initialize the development formatter

        Args:
            use_colors: Whether to use ANSI color codes
            include_context: Whether to include context information
        """
        self.use_colors = use_colors and self._supports_color()
        self.include_context = include_context

        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt=fmt, datefmt=datefmt)

    def _supports_color(self) -> bool:
        """Check if the terminal supports color"""
        # Disable colors if output is not to a terminal
        if not hasattr(sys.stdout, "isatty"):
            return False
        if not sys.stdout.isatty():
            return False

        # Check for Windows console
        if sys.platform == "win32":
            try:
                import colorama

                colorama.init()
                return True
            except ImportError:
                return False

        return True

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record for human readability

        Args:
            record: LogRecord to format

        Returns:
            Formatted string with optional color and context
        """
        # Get base formatted message
        base_message = super().format(record)

        # Add color if enabled
        if self.use_colors and record.levelname in self.COLORS:
            # Color just the level name
            level_color = self.COLORS[record.levelname]
            base_message = base_message.replace(
                record.levelname, f"{level_color}{record.levelname}{self.RESET}", 1
            )

        # Add context information if enabled and available
        if self.include_context:
            context_parts = []

            # Add request ID if available
            if hasattr(record, "request_id") and record.request_id:
                context_parts.append(f"req:{record.request_id[:8]}")

            # Add user ID if available
            if hasattr(record, "user_id") and record.user_id:
                context_parts.append(f"user:{str(record.user_id)[:8]}")

            # Add campaign ID if available
            if hasattr(record, "campaign_id") and record.campaign_id:
                context_parts.append(f"campaign:{str(record.campaign_id)[:8]}")

            # Add event type if available
            if hasattr(record, "event_type") and record.event_type:
                context_parts.append(f"type:{record.event_type}")

            # Add duration if available
            if hasattr(record, "duration_ms") and record.duration_ms:
                context_parts.append(f"dur:{record.duration_ms:.1f}ms")

            # Append context to message
            if context_parts:
                context_str = " | ".join(context_parts)
                base_message = f"{base_message} [{context_str}]"

        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            base_message = f"{base_message}\n{exc_text}"

        # Add stack info if present
        if record.stack_info:
            base_message = (
                f"{base_message}\nStack:\n{self.formatStack(record.stack_info)}"
            )

        return base_message

    def format_exception(self, exc_info) -> str:
        """Format exception with color if enabled"""
        exc_text = super().formatException(exc_info)

        if self.use_colors:
            # Color the exception text in red
            exc_text = f"{self.COLORS['ERROR']}{exc_text}{self.RESET}"

        return exc_text


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for high-volume logging
    Minimal overhead, suitable for performance-critical applications
    """

    def __init__(self):
        """Initialize compact formatter with minimal format"""
        fmt = "%(asctime)s|%(levelname)s|%(name)s|%(message)s"
        datefmt = "%H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)
