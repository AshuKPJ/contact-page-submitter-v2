# app/middleware/timeout.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import time
import traceback
from datetime import datetime


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle request timeouts and provide better error responses
    """

    def __init__(self, app, timeout: float = 30.0, debug: bool = False):
        super().__init__(app)
        self.timeout = timeout
        self.debug = debug

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_info = f"{request.method} {request.url.path}"

        if self.debug:
            print(
                f"[TIMEOUT] Starting request: {request_info} (timeout: {self.timeout}s)"
            )

        try:
            response = await asyncio.wait_for(call_next(request), timeout=self.timeout)

            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            if self.debug:
                print(
                    f"[TIMEOUT] Completed request: {request_info} in {process_time:.3f}s"
                )

            return response

        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            error_msg = (
                f"Request timeout after {process_time:.1f}s (limit: {self.timeout}s)"
            )

            print(f"[TIMEOUT] {error_msg} - {request_info}")

            return JSONResponse(
                status_code=408,
                content={
                    "detail": "Request timeout",
                    "timeout_seconds": self.timeout,
                    "elapsed_seconds": round(process_time, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path),
                    "method": request.method,
                },
                headers={
                    "X-Process-Time": f"{process_time:.3f}",
                    "X-Timeout": str(self.timeout),
                },
            )

        except Exception as e:
            process_time = time.time() - start_time
            error_type = type(e).__name__
            error_msg = str(e)

            print(
                f"[TIMEOUT] Error in request: {request_info} - {error_type}: {error_msg}"
            )

            if self.debug:
                print(f"[TIMEOUT] Full traceback:")
                traceback.print_exc()

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_type": error_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path),
                    "method": request.method,
                    "elapsed_seconds": round(process_time, 2),
                },
                headers={
                    "X-Process-Time": f"{process_time:.3f}",
                    "X-Error-Type": error_type,
                },
            )
