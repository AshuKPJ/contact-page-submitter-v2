# app/logging/decorators.py
"""
Enhanced logging decorators for automatic function logging
Provides decorators for logging function execution, exceptions, and performance
"""
import asyncio
import functools
import time
import traceback
from typing import Callable, Any, Optional, TypeVar, Union

from .core import get_logger, campaign_id_var, user_id_var, request_id_var

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def log_function(
    action: str,
    logger_name: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    sensitive_args: Optional[list] = None,
):
    """
    Decorator to log function execution with timing and context

    Args:
        action: Description of the action being performed
        logger_name: Optional custom logger name, defaults to function module
        log_args: Whether to log function arguments (be careful with sensitive data)
        log_result: Whether to log function result (be careful with sensitive data)
        sensitive_args: List of argument names that should not be logged

    Usage:
        @log_function("create_campaign")
        async def create_campaign(db: Session, current_user: User, ...):
            ...

        @log_function("process_payment", sensitive_args=["card_number", "cvv"])
        def process_payment(card_number: str, cvv: str, amount: float):
            ...
    """
    sensitive_args = sensitive_args or []

    def decorator(fn: F) -> F:
        logger = get_logger(logger_name or fn.__module__)

        # Extract function metadata
        func_module = fn.__module__
        func_name = fn.__name__
        func_qualname = fn.__qualname__

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                # Extract context from function arguments
                _extract_context(kwargs)

                # Generate unique execution ID
                execution_id = str(time.time())

                start_time = time.time()

                # Build safe context for logging
                safe_context = {
                    "event_type": "function_start",
                    "function": func_name,
                    "qualified_name": func_qualname,
                    "module": func_module,
                    "action": action,
                    "execution_id": execution_id,
                }

                # Add safe kwargs if requested
                if log_args:
                    safe_context["args"] = _sanitize_args(args, kwargs, sensitive_args)

                logger.info(f"Function started: {action}", context=safe_context)

                try:
                    result = await fn(*args, **kwargs)

                    duration_ms = (time.time() - start_time) * 1000

                    # Log performance metric
                    logger.performance_metric(
                        f"{action}_duration", duration_ms, execution_id=execution_id
                    )

                    success_context = {
                        "event_type": "function_success",
                        "function": func_name,
                        "action": action,
                        "duration_ms": duration_ms,
                        "execution_id": execution_id,
                    }

                    if log_result and result is not None:
                        success_context["result_type"] = type(result).__name__
                        # Only log simple types
                        if isinstance(result, (str, int, float, bool, list, dict)):
                            success_context["result_preview"] = str(result)[:100]

                    logger.info(
                        f"Function completed: {action}", context=success_context
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    error_context = {
                        "event_type": "function_error",
                        "function": func_name,
                        "action": action,
                        "duration_ms": duration_ms,
                        "execution_id": execution_id,
                        "traceback": traceback.format_exc(),
                    }

                    logger.exception(e, handled=False, context=error_context)
                    raise

            return async_wrapper
        else:

            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                # Similar implementation for sync functions
                _extract_context(kwargs)

                execution_id = str(time.time())
                start_time = time.time()

                safe_context = {
                    "event_type": "function_start",
                    "function": func_name,
                    "qualified_name": func_qualname,
                    "module": func_module,
                    "action": action,
                    "execution_id": execution_id,
                }

                if log_args:
                    safe_context["args"] = _sanitize_args(args, kwargs, sensitive_args)

                logger.info(f"Function started: {action}", context=safe_context)

                try:
                    result = fn(*args, **kwargs)

                    duration_ms = (time.time() - start_time) * 1000

                    logger.performance_metric(
                        f"{action}_duration", duration_ms, execution_id=execution_id
                    )

                    success_context = {
                        "event_type": "function_success",
                        "function": func_name,
                        "action": action,
                        "duration_ms": duration_ms,
                        "execution_id": execution_id,
                    }

                    if log_result and result is not None:
                        success_context["result_type"] = type(result).__name__
                        if isinstance(result, (str, int, float, bool, list, dict)):
                            success_context["result_preview"] = str(result)[:100]

                    logger.info(
                        f"Function completed: {action}", context=success_context
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    error_context = {
                        "event_type": "function_error",
                        "function": func_name,
                        "action": action,
                        "duration_ms": duration_ms,
                        "execution_id": execution_id,
                        "traceback": traceback.format_exc(),
                    }

                    logger.exception(e, handled=False, context=error_context)
                    raise

            return sync_wrapper

    return decorator


def log_exceptions(
    action: str, logger_name: Optional[str] = None, include_traceback: bool = True
):
    """
    Decorator to only log exceptions (lighter weight than log_function)

    Args:
        action: Description of the action for context
        logger_name: Optional custom logger name
        include_traceback: Whether to include full traceback

    Usage:
        @log_exceptions("submit_form")
        async def submit_form(...):
            ...
    """

    def decorator(fn: F) -> F:
        logger = get_logger(logger_name or fn.__module__)

        func_module = fn.__module__
        func_name = fn.__name__

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    # Extract context
                    _extract_context(kwargs)

                    context = {
                        "event_type": "function_exception",
                        "function": func_name,
                        "module": func_module,
                        "action": action,
                    }

                    if include_traceback:
                        context["traceback"] = traceback.format_exc()

                    logger.exception(e, handled=False, context=context)
                    raise

            return async_wrapper
        else:

            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    # Extract context
                    _extract_context(kwargs)

                    context = {
                        "event_type": "function_exception",
                        "function": func_name,
                        "module": func_module,
                        "action": action,
                    }

                    if include_traceback:
                        context["traceback"] = traceback.format_exc()

                    logger.exception(e, handled=False, context=context)
                    raise

            return sync_wrapper

    return decorator


def log_performance(
    action: str, logger_name: Optional[str] = None, threshold_ms: Optional[float] = None
):
    """
    Decorator to only log performance metrics (minimal overhead)

    Args:
        action: Description of the action being measured
        logger_name: Optional custom logger name
        threshold_ms: Only log if execution time exceeds this threshold

    Usage:
        @log_performance("database_query", threshold_ms=100)
        def expensive_database_operation():
            ...
    """

    def decorator(fn: F) -> F:
        logger = get_logger(logger_name or fn.__module__)

        if asyncio.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True

                try:
                    result = await fn(*args, **kwargs)
                    return result
                except Exception:
                    success = False
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000

                    # Only log if above threshold (if set)
                    if threshold_ms is None or duration_ms >= threshold_ms:
                        logger.performance_metric(
                            f"{action}_duration", duration_ms, success=success
                        )

            return async_wrapper
        else:

            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True

                try:
                    result = fn(*args, **kwargs)
                    return result
                except Exception:
                    success = False
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000

                    if threshold_ms is None or duration_ms >= threshold_ms:
                        logger.performance_metric(
                            f"{action}_duration", duration_ms, success=success
                        )

            return sync_wrapper

    return decorator


# Helper functions
def _extract_context(kwargs: dict) -> None:
    """Extract and set context variables from function kwargs"""
    current_user = kwargs.get("current_user")
    campaign_id = kwargs.get("campaign_id")
    request = kwargs.get("request")

    if current_user:
        try:
            user_id_var.set(str(getattr(current_user, "id", "unknown")))
        except Exception:
            pass

    if campaign_id:
        try:
            campaign_id_var.set(str(campaign_id))
        except Exception:
            pass

    if request:
        try:
            # Try to get request ID from headers or state
            request_id = None
            if hasattr(request, "headers"):
                request_id = request.headers.get("X-Request-ID")
            if not request_id and hasattr(request, "state"):
                request_id = getattr(request.state, "request_id", None)

            if request_id:
                request_id_var.set(str(request_id))
        except Exception:
            pass


def _sanitize_args(args: tuple, kwargs: dict, sensitive_args: list) -> dict:
    """Sanitize arguments for logging, removing sensitive data"""
    safe_args = {}

    # Process kwargs
    for key, value in kwargs.items():
        if key in sensitive_args:
            safe_args[key] = "***REDACTED***"
        elif key in ["password", "token", "secret", "api_key", "db", "session"]:
            safe_args[key] = "***REDACTED***"
        elif isinstance(value, (str, int, float, bool, type(None))):
            safe_args[key] = str(value)[:100] if isinstance(value, str) else value
        else:
            safe_args[key] = f"<{type(value).__name__}>"

    # Add positional args count
    if args:
        safe_args["_positional_args_count"] = len(args)

    return safe_args
