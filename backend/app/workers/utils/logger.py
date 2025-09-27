# app/workers/utils/logger.py
"""Worker logger implementation for automation logging."""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any


class WorkerLogger:
    """Enhanced logger for worker processes."""

    def __init__(
        self, user_id: Optional[str] = None, campaign_id: Optional[str] = None
    ):
        self.user_id = user_id
        self.campaign_id = campaign_id

        # Create logger name
        logger_name = "worker"
        if campaign_id:
            logger_name += f".{campaign_id[:8]}"
        if user_id:
            logger_name += f".{user_id[:8]}"

        self.logger = logging.getLogger(logger_name)

        # Set up logger if not already configured
        if not self.logger.handlers:
            self._setup_logger()

    def _setup_logger(self):
        """Set up the logger with appropriate handlers and formatting."""
        self.logger.setLevel(logging.INFO)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(handler)

    def _get_context(self) -> Dict[str, Any]:
        """Get logging context."""
        context = {}
        if self.user_id:
            context["user_id"] = self.user_id[:8]
        if self.campaign_id:
            context["campaign_id"] = self.campaign_id[:8]
        return context

    def _format_message(
        self, message: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format message with context."""
        log_context = self._get_context()
        if context:
            log_context.update(context)

        if log_context:
            context_str = " | ".join([f"{k}={v}" for k, v in log_context.items()])
            return f"[{context_str}] {message}"
        return message

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        formatted_message = self._format_message(message, context)
        self.logger.info(formatted_message)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        formatted_message = self._format_message(message, context)
        self.logger.warning(formatted_message)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log error message."""
        formatted_message = self._format_message(message, context)
        self.logger.error(formatted_message)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        formatted_message = self._format_message(message, context)
        self.logger.debug(formatted_message)

    def database_operation(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        affected_rows: int,
        success: bool,
    ):
        """Log database operation."""
        status = "SUCCESS" if success else "FAILED"
        message = f"DB {operation} on {table}: {duration_ms:.2f}ms, {affected_rows} rows, {status}"
        self.info(message)


# Create a simple function to get a logger
def get_worker_logger(
    name: str, user_id: Optional[str] = None, campaign_id: Optional[str] = None
) -> WorkerLogger:
    """Get a worker logger instance."""
    return WorkerLogger(user_id=user_id, campaign_id=campaign_id)
