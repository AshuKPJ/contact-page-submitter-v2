# app/middleware/__init__.py
"""
Middleware package for the application
Uses the proper logging system from app.logging
"""

from .cors import setup_cors
from .timeout import TimeoutMiddleware

# Import the proper LoggingMiddleware from your logging package
from app.logging.middleware import LoggingMiddleware

# Backwards compatibility alias
DevelopmentLoggingMiddleware = LoggingMiddleware

__all__ = [
    "setup_cors",
    "TimeoutMiddleware",
    "LoggingMiddleware",
    "DevelopmentLoggingMiddleware",
]
