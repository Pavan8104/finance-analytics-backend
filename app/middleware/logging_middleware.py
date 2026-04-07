"""
Structured request/response logging middleware.

Logs every inbound HTTP request with:
  - HTTP method and path
  - Query string (if present)
  - Response status code
  - Request duration in milliseconds
  - Client IP address

Sensitive paths (e.g. /auth/login) never log request bodies.
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that logs each HTTP request/response cycle."""

    # Paths whose bodies we should NEVER log (contains credentials)
    _SENSITIVE_PATHS = {"/api/v1/auth/login", "/api/v1/auth/refresh"}

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # --- Process the request ---
        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status_code = response.status_code

        # Choose log level based on status code
        log_fn = logger.info
        if status_code >= 500:
            log_fn = logger.error
        elif status_code >= 400:
            log_fn = logger.warning

        log_fn(
            f"{request.method} {request.url.path} → {status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        # Inject server timing header for observability
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
