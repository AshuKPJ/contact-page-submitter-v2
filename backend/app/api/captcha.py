"""Enhanced Captcha API endpoints with comprehensive logging for FastAPI."""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from functools import wraps
import time
from typing import Dict, Any, Optional
import secrets
import random
from datetime import datetime, timedelta
import logging

# Import dependencies - adjust based on your actual project structure
try:
    from app.core.dependencies import get_current_user
    from app.logging import get_logger, log_function, log_exceptions

    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

    # Fallback if dependencies not available
    def get_current_user():
        return None

    def get_logger(name):
        return logging.getLogger(name)


# Initialize logger
logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter(
    prefix="/api/captcha",
    tags=["captcha"],
    responses={404: {"description": "Not found"}},
)

# Simulated captcha storage (in production, use Redis or similar)
CAPTCHA_STORE = {}
CAPTCHA_ATTEMPTS = {}
MAX_ATTEMPTS = 5
CAPTCHA_LIFETIME = 300  # 5 minutes


# Pydantic models for request/response
class CaptchaGenerateResponse(BaseModel):
    success: bool
    captcha_id: Optional[str] = None
    challenge: Optional[str] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None


class CaptchaVerifyRequest(BaseModel):
    captcha_id: str
    answer: str


class CaptchaVerifyResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    attempts_remaining: Optional[int] = None


class CaptchaStatsResponse(BaseModel):
    success: bool
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def log_performance(operation: str, duration: float, context: Dict[str, Any]):
    """Log performance metrics for slow operations."""
    logger.warning(
        f"Slow operation detected: {operation}",
        extra={
            "operation": operation,
            "duration": duration,
            "threshold": 1.0,
            **context,
        },
    )


def log_security_event(
    event_type: str, context: Dict[str, Any], severity: str = "warning"
):
    """Log security-related events."""
    log_method = getattr(logger, severity, logger.warning)
    log_method(
        f"Security event: {event_type}",
        extra={"event_type": event_type, "severity": severity, **context},
    )


def clean_expired_captchas():
    """Clean up expired captchas from storage."""
    current_time = time.time()
    expired = []

    for captcha_id, data in list(CAPTCHA_STORE.items()):
        if current_time - data["created"] > CAPTCHA_LIFETIME:
            expired.append(captcha_id)

    for captcha_id in expired:
        del CAPTCHA_STORE[captcha_id]
        if captcha_id in CAPTCHA_ATTEMPTS:
            del CAPTCHA_ATTEMPTS[captcha_id]

    if expired:
        logger.info(f"Cleaned {len(expired)} expired captchas")


@router.post("/generate", response_model=CaptchaGenerateResponse)
async def generate_captcha(request: Request):
    """Generate a new captcha challenge."""
    start_time = time.time()

    try:
        # Clean expired captchas periodically
        clean_expired_captchas()

        # Generate captcha
        captcha_id = secrets.token_urlsafe(32)

        # Simple math captcha for demonstration
        num1 = random.randint(1, 50)
        num2 = random.randint(1, 50)
        operation = random.choice(["+", "-", "*"])

        if operation == "+":
            answer = num1 + num2
            question = f"{num1} + {num2}"
        elif operation == "-":
            answer = num1 - num2
            question = f"{num1} - {num2}"
        else:
            answer = num1 * num2
            question = f"{num1} × {num2}"

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Store captcha
        CAPTCHA_STORE[captcha_id] = {
            "answer": str(answer),
            "created": time.time(),
            "ip": client_ip,
            "attempts": 0,
        }

        logger.info(
            "Captcha generated successfully",
            extra={
                "captcha_id": captcha_id[:8] + "...",
                "ip": client_ip,
                "type": "math",
                "duration": time.time() - start_time,
            },
        )

        return CaptchaGenerateResponse(
            success=True,
            captcha_id=captcha_id,
            challenge=question,
            expires_in=CAPTCHA_LIFETIME,
        )

    except Exception as e:
        logger.error(
            "Failed to generate captcha",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": time.time() - start_time,
            },
            exc_info=True,
        )
        return CaptchaGenerateResponse(
            success=False, error="Failed to generate captcha"
        )


@router.post("/verify", response_model=CaptchaVerifyResponse)
async def verify_captcha(data: CaptchaVerifyRequest, request: Request):
    """Verify a captcha response."""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"

    try:
        captcha_id = data.captcha_id
        answer = data.answer

        # Check if captcha exists
        if captcha_id not in CAPTCHA_STORE:
            logger.warning(
                "Invalid or expired captcha ID",
                extra={
                    "captcha_id": (
                        captcha_id[:8] + "..." if len(captcha_id) > 8 else captcha_id
                    ),
                    "ip": client_ip,
                },
            )

            log_security_event(
                event_type="captcha_invalid",
                context={
                    "captcha_id": (
                        captcha_id[:8] + "..." if len(captcha_id) > 8 else captcha_id
                    ),
                    "ip": client_ip,
                },
                severity="warning",
            )

            raise HTTPException(status_code=400, detail="Invalid or expired captcha")

        captcha_data = CAPTCHA_STORE[captcha_id]

        # Check expiration
        if time.time() - captcha_data["created"] > CAPTCHA_LIFETIME:
            del CAPTCHA_STORE[captcha_id]
            if captcha_id in CAPTCHA_ATTEMPTS:
                del CAPTCHA_ATTEMPTS[captcha_id]

            logger.warning(
                "Captcha expired",
                extra={
                    "captcha_id": captcha_id[:8] + "...",
                    "age": time.time() - captcha_data["created"],
                    "ip": client_ip,
                },
            )

            raise HTTPException(status_code=400, detail="Captcha expired")

        # Track attempts
        if captcha_id not in CAPTCHA_ATTEMPTS:
            CAPTCHA_ATTEMPTS[captcha_id] = 0

        CAPTCHA_ATTEMPTS[captcha_id] += 1
        current_attempts = CAPTCHA_ATTEMPTS[captcha_id]

        # Check attempt limit
        if current_attempts > MAX_ATTEMPTS:
            del CAPTCHA_STORE[captcha_id]
            del CAPTCHA_ATTEMPTS[captcha_id]

            logger.warning(
                "Captcha max attempts exceeded",
                extra={
                    "captcha_id": captcha_id[:8] + "...",
                    "attempts": current_attempts,
                    "ip": client_ip,
                },
            )

            log_security_event(
                event_type="captcha_max_attempts",
                context={
                    "captcha_id": captcha_id[:8] + "...",
                    "ip": client_ip,
                    "attempts": MAX_ATTEMPTS,
                },
                severity="warning",
            )

            raise HTTPException(status_code=429, detail="Too many attempts")

        # Verify answer
        if str(answer) == str(captcha_data["answer"]):
            # Remove used captcha
            del CAPTCHA_STORE[captcha_id]
            if captcha_id in CAPTCHA_ATTEMPTS:
                del CAPTCHA_ATTEMPTS[captcha_id]

            logger.info(
                "Captcha verified successfully",
                extra={
                    "captcha_id": captcha_id[:8] + "...",
                    "attempts": current_attempts,
                    "ip": client_ip,
                    "duration": time.time() - start_time,
                },
            )

            return CaptchaVerifyResponse(success=True, message="Captcha verified")
        else:
            logger.warning(
                "Captcha verification failed",
                extra={
                    "captcha_id": captcha_id[:8] + "...",
                    "attempts": current_attempts,
                    "ip": client_ip,
                },
            )

            return CaptchaVerifyResponse(
                success=False,
                error="Incorrect answer",
                attempts_remaining=MAX_ATTEMPTS - current_attempts,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Captcha verification error",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "ip": client_ip,
                "duration": time.time() - start_time,
            },
            exc_info=True,
        )
        return CaptchaVerifyResponse(success=False, error="Verification failed")


@router.get("/stats", response_model=CaptchaStatsResponse)
async def get_captcha_stats(
    current_user: Optional[Dict] = Depends(get_current_user) if HAS_AUTH else None,
):
    """Get captcha statistics (admin only)."""
    try:
        # Check admin permission (implement your own logic)
        # if current_user and not is_admin(current_user.get("id")):
        #     raise HTTPException(status_code=403, detail="Unauthorized")

        stats = {
            "active_captchas": len(CAPTCHA_STORE),
            "pending_verifications": len(CAPTCHA_ATTEMPTS),
            "total_attempts": sum(CAPTCHA_ATTEMPTS.values()),
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Captcha stats retrieved",
            extra={
                **stats,
                "user_id": current_user.get("id") if current_user else "anonymous",
            },
        )

        return CaptchaStatsResponse(success=True, stats=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get captcha stats",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": current_user.get("id") if current_user else None,
            },
            exc_info=True,
        )
        return CaptchaStatsResponse(success=False, error="Failed to retrieve stats")


def is_admin(user_id: str) -> bool:
    """
    Check if user is admin.
    TODO: Implement your own admin check logic here.
    """
    # Example implementation - replace with your actual logic
    # return user_id in ADMIN_USERS
    return False


# Health check endpoint for this router
@router.get("/health")
async def captcha_health():
    """Check captcha service health."""
    return {
        "status": "healthy",
        "active_captchas": len(CAPTCHA_STORE),
        "pending_verifications": len(CAPTCHA_ATTEMPTS),
    }
