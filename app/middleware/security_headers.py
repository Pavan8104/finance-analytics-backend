"""
Security Headers Middleware.

Adds industry-standard HTTP security headers to every response.
These headers are validated by tools like Mozilla Observatory and securityheaders.com.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response
from typing import Callable


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects HTTP security headers on every response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Prevent browsers from MIME-sniffing a response away from declared content-type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking via iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Force HTTPS for 1 year (only effective in production behind TLS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Restrict what browser features this app can use
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), payment=()"
        )

        # Control what referrer info is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server fingerprint headers (MutableHeaders doesn't support .pop())
        try:
            del response.headers["server"]
        except KeyError:
            pass
        try:
            del response.headers["x-powered-by"]
        except KeyError:
            pass

        # Content Security Policy
        # Allows Swagger UI and ReDoc docs to function (inline styles + CDN scripts)
        # For pure API (no docs) deployments, replace with: "default-src 'none'; frame-ancestors 'none'"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "frame-ancestors 'none'"
        )

        return response
