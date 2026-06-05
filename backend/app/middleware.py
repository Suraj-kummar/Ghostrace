"""
ghostrace.backend.middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Custom ASGI middleware for cross-cutting concerns:
  - Request timing (adds X-Process-Time header)
  - Unique request ID (adds X-Request-ID header)
"""
from __future__ import annotations

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger()


class TimingMiddleware(BaseHTTPMiddleware):
    """Injects X-Process-Time (ms) into every response and logs slow requests."""

    SLOW_THRESHOLD_MS: float = 2000.0  # warn if request takes > 2s

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Process-Time"] = f"{elapsed_ms}ms"

        if elapsed_ms > self.SLOW_THRESHOLD_MS:
            logger.warning(
                "slow_request",
                method=request.method,
                path=request.url.path,
                elapsed_ms=elapsed_ms,
            )
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID into every request/response pair."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
