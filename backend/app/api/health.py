"""Enhanced Health Check API endpoints for FastAPI with comprehensive logging."""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import psutil
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
import logging
import asyncio


# Import dependencies - adjust based on your actual project structure
try:
    from app.core.dependencies import get_current_user
    from app.logging import get_logger

    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

    # Fallback if dependencies not available
    def get_current_user():
        return {"id": "anonymous"}

    def get_logger(name):
        return logging.getLogger(name)


# Initialize logger
logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter(
    prefix="/api/health",
    tags=["health"],
    responses={503: {"description": "Service Unavailable"}},
)

# Health check cache
HEALTH_CACHE = {"last_check": None, "results": {}, "cache_duration": 10}  # seconds


# Pydantic models for responses
class HealthStatus(BaseModel):
    status: str
    timestamp: str
    uptime_seconds: Optional[float] = None
    service: Optional[str] = None


class ServiceHealth(BaseModel):
    status: str
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    timestamp: str


class SystemResources(BaseModel):
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]


class DetailedHealth(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, Any]
    uptime_seconds: float


class ReadinessResponse(BaseModel):
    ready: bool
    timestamp: str
    reason: Optional[str] = None


class LivenessResponse(BaseModel):
    alive: bool
    timestamp: str
    error: Optional[str] = None


class MetricsResponse(BaseModel):
    success: bool
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def log_performance(operation: str, duration: float, context: Dict[str, Any]):
    """Log performance metrics for slow operations."""
    logger.warning(
        f"Slow operation detected: {operation}",
        extra={
            "operation": operation,
            "duration": duration,
            "threshold": 2.0,
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


async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    start_time = time.time()

    try:
        # Replace with actual database check
        # from app.core.database import get_db
        # async with get_db() as db:
        #     await db.execute("SELECT 1")

        # Simulated check
        await asyncio.sleep(0.01)  # Simulate DB query

        response_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.debug(
            "Database health check passed",
            extra={"response_time_ms": response_time, "status": "healthy"},
        )

        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(
            "Database health check failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        # Replace with actual Redis check
        # import aioredis
        # redis = await aioredis.create_redis_pool('redis://localhost')
        # await redis.ping()
        # redis.close()
        # await redis.wait_closed()

        # Simulated check
        import asyncio

        await asyncio.sleep(0.01)  # Simulate Redis ping

        logger.debug("Redis health check passed")

        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(
            "Redis health check failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def check_system_resources() -> Dict[str, Any]:
    """Check system resource utilization."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        resources = {
            "cpu": {
                "usage_percent": cpu_percent,
                "status": (
                    "healthy"
                    if cpu_percent < 80
                    else "warning" if cpu_percent < 95 else "critical"
                ),
            },
            "memory": {
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "status": (
                    "healthy"
                    if memory.percent < 80
                    else "warning" if memory.percent < 95 else "critical"
                ),
            },
            "disk": {
                "usage_percent": disk.percent,
                "available_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "status": (
                    "healthy"
                    if disk.percent < 80
                    else "warning" if disk.percent < 95 else "critical"
                ),
            },
        }

        # Log warnings for high resource usage
        if cpu_percent > 80:
            logger.warning(
                "High CPU usage detected", extra={"cpu_percent": cpu_percent}
            )

        if memory.percent > 80:
            logger.warning(
                "High memory usage detected", extra={"memory_percent": memory.percent}
            )

        if disk.percent > 80:
            logger.warning(
                "High disk usage detected", extra={"disk_percent": disk.percent}
            )

        return resources

    except Exception as e:
        logger.error(
            "System resource check failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        return {"status": "error", "error": str(e)}


@router.get("/check", response_model=HealthStatus)
async def basic_health_check(request: Request):
    """Basic health check endpoint."""
    start_time = time.time()

    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.info("Basic health check requested", extra={"ip": client_ip})

        result = HealthStatus(
            status="healthy",
            service="api",
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=time.time() - psutil.boot_time(),
        )

        duration = time.time() - start_time
        logger.info(
            "Basic health check completed",
            extra={"duration": duration, "status": "healthy", "ip": client_ip},
        )

        return result

    except Exception as e:
        logger.error(
            "Basic health check failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/detailed", response_model=DetailedHealth)
async def detailed_health_check(request: Request):
    """Detailed health check with all service dependencies."""
    start_time = time.time()

    try:
        client_ip = request.client.host if request.client else "unknown"

        # Check cache
        if HEALTH_CACHE["last_check"]:
            cache_age = time.time() - HEALTH_CACHE["last_check"]
            if cache_age < HEALTH_CACHE["cache_duration"]:
                logger.info(
                    "Returning cached health check results",
                    extra={"cache_age": cache_age, "ip": client_ip},
                )
                return HEALTH_CACHE["results"]

        logger.info("Performing detailed health check", extra={"ip": client_ip})

        # Perform all health checks
        import asyncio

        database_health, redis_health = await asyncio.gather(
            check_database_health(), check_redis_health()
        )

        checks = {
            "database": database_health,
            "redis": redis_health,
            "system": check_system_resources(),
        }

        # Determine overall health
        overall_status = "healthy"
        for service, status in checks.items():
            if isinstance(status, dict) and status.get("status") == "unhealthy":
                overall_status = "degraded"
                break
            elif isinstance(status, dict) and status.get("status") == "critical":
                overall_status = "critical"
                break

        response = DetailedHealth(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            services=checks,
            uptime_seconds=time.time() - psutil.boot_time(),
        )

        # Update cache
        HEALTH_CACHE["last_check"] = time.time()
        HEALTH_CACHE["results"] = response

        # Log overall health status
        duration = time.time() - start_time
        logger.info(
            "Detailed health check completed",
            extra={
                "overall_status": overall_status,
                "services_checked": list(checks.keys()),
                "ip": client_ip,
                "duration": duration,
            },
        )

        if duration > 2.0:
            log_performance(
                operation="detailed_health_check",
                duration=duration,
                context={"status": overall_status},
            )

        if overall_status != "healthy":
            raise HTTPException(status_code=503, detail=response.dict())

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Detailed health check error",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check(request: Request):
    """Kubernetes readiness probe endpoint."""
    try:
        client_ip = request.client.host if request.client else "unknown"

        # Check if service is ready to accept traffic
        db_health = await check_database_health()

        if db_health["status"] == "healthy":
            logger.info("Readiness check passed", extra={"ip": client_ip})
            return ReadinessResponse(
                ready=True, timestamp=datetime.utcnow().isoformat()
            )
        else:
            logger.warning(
                "Readiness check failed",
                extra={"reason": "database_unhealthy", "ip": client_ip},
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "ready": False,
                    "reason": "Database not ready",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Readiness check error",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/liveness", response_model=LivenessResponse)
async def liveness_check(request: Request):
    """Kubernetes liveness probe endpoint."""
    try:
        client_ip = request.client.host if request.client else "unknown"
        logger.debug("Liveness check requested", extra={"ip": client_ip})

        return LivenessResponse(alive=True, timestamp=datetime.utcnow().isoformat())

    except Exception as e:
        logger.error(
            "Liveness check failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=503,
            detail={
                "alive": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/metrics", response_model=MetricsResponse)
async def get_health_metrics(
    request: Request,
    current_user: Optional[Dict] = Depends(get_current_user) if HAS_AUTH else None,
):
    """Get detailed health metrics (admin only)."""
    try:
        user_id = current_user.get("id") if current_user else "anonymous"

        # TODO: Add admin check
        # if not is_admin(user_id):
        #     raise HTTPException(status_code=403, detail="Unauthorized")

        # Collect detailed metrics
        import asyncio

        database_health, redis_health = await asyncio.gather(
            check_database_health(), check_redis_health()
        )

        metrics = {
            "system": check_system_resources(),
            "services": {"database": database_health, "redis": redis_health},
            "process": {
                "pid": os.getpid(),
                "cpu_percent": psutil.Process().cpu_percent(),
                "memory_mb": round(psutil.Process().memory_info().rss / (1024**2), 2),
                "num_threads": psutil.Process().num_threads(),
                "open_files": len(psutil.Process().open_files()),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Health metrics retrieved",
            extra={"user_id": user_id, "metrics_collected": list(metrics.keys())},
        )

        return MetricsResponse(success=True, metrics=metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get health metrics",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "user_id": current_user.get("id") if current_user else None,
            },
        )
        return MetricsResponse(success=False, error="Failed to retrieve metrics")


# Add a simple ping endpoint
@router.get("/ping")
async def ping():
    """Simple ping endpoint for quick checks."""
    return {"pong": True, "timestamp": datetime.utcnow().isoformat()}
