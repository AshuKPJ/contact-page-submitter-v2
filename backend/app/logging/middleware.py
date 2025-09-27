# app/logging/middleware.py
"""
Enhanced logging middleware for FastAPI
Provides comprehensive request/response logging with performance tracking
"""
import time
import uuid
import json
from typing import Callable, Optional, Dict, Any, List
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import Headers
import asyncio

from .core import get_logger, request_id_var, user_id_var, campaign_id_var


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced logging middleware with structured logging
    Tracks requests, responses, performance, and errors
    """

    # Headers to exclude from logging (case-insensitive)
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-csrf-token",
    }

    # Paths to skip logging (e.g., health checks)
    SKIP_PATHS = {
        "/health",
        "/ping",
        "/metrics",
        "/favicon.ico",
    }

    def __init__(
        self,
        app,
        logger_name: str = "http",
        log_request_body: bool = False,
        log_response_body: bool = False,
        log_headers: bool = True,
        skip_paths: Optional[List[str]] = None,
        slow_request_threshold_ms: float = 1000,
    ):
        """
        Initialize logging middleware

        Args:
            app: FastAPI application
            logger_name: Name for the logger
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            log_headers: Whether to log headers
            skip_paths: Additional paths to skip logging
            slow_request_threshold_ms: Threshold for slow request warnings
        """
        super().__init__(app)
        self.logger = get_logger(logger_name)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.log_headers = log_headers
        self.slow_request_threshold_ms = slow_request_threshold_ms

        # Combine skip paths
        self.skip_paths = self.SKIP_PATHS.copy()
        if skip_paths:
            self.skip_paths.update(skip_paths)

        # Statistics
        self.request_count = 0
        self.error_count = 0
        self.slow_request_count = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request and response

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response object
        """
        # Check if we should skip logging for this path
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Store request ID in request state for access by handlers
        request.state.request_id = request_id

        # Try to extract user ID from request
        user_id = await self._extract_user_id(request)
        if user_id:
            user_id_var.set(user_id)
            request.state.user_id = user_id

        # Try to extract campaign ID from request
        campaign_id = self._extract_campaign_id(request)
        if campaign_id:
            campaign_id_var.set(campaign_id)
            request.state.campaign_id = campaign_id

        # Track request count
        self.request_count += 1

        # Start timing
        start_time = time.time()

        # Extract request information
        request_info = await self._extract_request_info(request)

        # Log request start
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            context={
                "event_type": "http_request_start",
                "request_id": request_id,
                **request_info,
            },
        )

        # Store request body if needed
        request_body = None
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            request_body = await self._get_request_body(request)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Check if slow request
            is_slow = duration_ms > self.slow_request_threshold_ms
            if is_slow:
                self.slow_request_count += 1

            # Extract response info
            response_info = self._extract_response_info(response, duration_ms)

            # Log appropriate level based on status and performance
            if response.status_code >= 500:
                self.error_count += 1
                log_level = "ERROR"
                event_type = "http_request_error"
            elif response.status_code >= 400:
                log_level = "WARNING"
                event_type = "http_request_client_error"
            elif is_slow:
                log_level = "WARNING"
                event_type = "http_request_slow"
            else:
                log_level = "INFO"
                event_type = "http_request_success"

            # Build log context
            log_context = {
                "event_type": event_type,
                "request_id": request_id,
                **request_info,
                **response_info,
            }

            # Add request body if configured
            if self.log_request_body and request_body is not None:
                log_context["request_body"] = self._sanitize_body(request_body)

            # Log based on level
            message = (
                f"Request completed: {response.status_code} in {duration_ms:.2f}ms"
            )
            if is_slow:
                message = f"SLOW {message}"

            getattr(self.logger, log_level.lower())(message, context=log_context)

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # Add server timing header for performance monitoring
            response.headers["Server-Timing"] = f"total;dur={duration_ms:.2f}"

            return response

        except Exception as e:
            # Calculate duration for errors
            duration_ms = (time.time() - start_time) * 1000
            self.error_count += 1

            # Log error with full context
            self.logger.error(
                f"Request failed: {str(e)}",
                context={
                    "event_type": "http_request_exception",
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": duration_ms,
                    **request_info,
                    "request_body": (
                        self._sanitize_body(request_body) if request_body else None
                    ),
                },
            )

            # Re-raise the exception
            raise

    async def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract request information for logging"""
        info = {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": (
                dict(request.query_params) if request.query_params else None
            ),
            "path_params": (
                request.path_params if hasattr(request, "path_params") else None
            ),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "")[:200],
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }

        # Add headers if configured
        if self.log_headers:
            info["headers"] = self._sanitize_headers(request.headers)

        # Clean up None values
        return {k: v for k, v in info.items() if v is not None}

    def _extract_response_info(
        self, response: Response, duration_ms: float
    ) -> Dict[str, Any]:
        """Extract response information for logging"""
        info = {
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size": response.headers.get("content-length"),
            "content_type": response.headers.get("content-type"),
        }

        # Clean up None values
        return {k: v for k, v in info.items() if v is not None}

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check X-Forwarded-For header (from proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

    def _sanitize_headers(self, headers: Headers) -> Dict[str, str]:
        """Sanitize headers for logging, removing sensitive values"""
        sanitized = {}

        for name, value in headers.items():
            name_lower = name.lower()

            # Skip or redact sensitive headers
            if name_lower in self.SENSITIVE_HEADERS:
                sanitized[name] = "***REDACTED***"
            elif "token" in name_lower or "key" in name_lower or "secret" in name_lower:
                sanitized[name] = "***REDACTED***"
            else:
                # Truncate long header values
                sanitized[name] = value[:200] if len(value) > 200 else value

        return sanitized

    def _sanitize_body(self, body: Any, max_length: int = 1000) -> Any:
        """Sanitize request/response body for logging"""
        if body is None:
            return None

        # Convert to string if needed
        if isinstance(body, bytes):
            try:
                body = body.decode("utf-8")
            except:
                return "<binary data>"

        body_str = str(body)

        # Truncate if too long
        if len(body_str) > max_length:
            return body_str[:max_length] + "...(truncated)"

        # Try to parse as JSON and remove sensitive fields
        try:
            if isinstance(body, str):
                body_dict = json.loads(body)
            else:
                body_dict = body

            if isinstance(body_dict, dict):
                # Remove sensitive fields
                sensitive_fields = [
                    "password",
                    "token",
                    "api_key",
                    "secret",
                    "credit_card",
                ]
                for field in sensitive_fields:
                    if field in body_dict:
                        body_dict[field] = "***REDACTED***"

                return body_dict
        except:
            pass

        return body_str

    async def _get_request_body(self, request: Request) -> Optional[bytes]:
        """Get request body for logging"""
        try:
            # Store the body for later use by the actual handler
            body = await request.body()

            # Create a new receive function that returns the stored body
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive
            return body
        except:
            return None

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from request
        Override this method based on your authentication system
        """
        # Try JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Import your JWT decoding function
                # from app.core.auth import decode_token
                # token = auth_header.split(" ")[1]
                # payload = decode_token(token)
                # return payload.get("user_id")
                pass
            except:
                pass

        # Try session/cookie
        try:
            # from app.core.session import get_session_user
            # user_id = get_session_user(request)
            # return user_id
            pass
        except:
            pass

        # Try from request state if set by auth middleware
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "id"):
                return str(user.id)

        return None

    def _extract_campaign_id(self, request: Request) -> Optional[str]:
        """Extract campaign ID from request path or query parameters"""
        # Try path parameters
        if hasattr(request, "path_params"):
            campaign_id = request.path_params.get("campaign_id")
            if campaign_id:
                return str(campaign_id)

        # Try query parameters
        campaign_id = request.query_params.get("campaign_id")
        if campaign_id:
            return str(campaign_id)

        # Try from request state
        if hasattr(request.state, "campaign_id"):
            return str(request.state.campaign_id)

        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get middleware statistics

        Returns:
            Dictionary containing middleware stats
        """
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": (
                (self.error_count / self.request_count * 100)
                if self.request_count > 0
                else 0
            ),
            "slow_request_count": self.slow_request_count,
            "slow_request_rate": (
                (self.slow_request_count / self.request_count * 100)
                if self.request_count > 0
                else 0
            ),
            "slow_request_threshold_ms": self.slow_request_threshold_ms,
        }
