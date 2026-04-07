"""
Finance Analytics API — Application Entry Point

Startup order:
  1. Logger initialized
  2. DB tables created (dev/test) or checked
  3. Middleware registered (security headers, request logging, CORS)
  4. Rate limiter registered
  5. Exception handlers registered
  6. Routers mounted at /api/v1
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import register_exception_handlers
from app.api.api_v1 import api_router
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Global rate limiter — keyed on client IP
# Modify key_func for authenticated-user-based limiting in the future
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


# ---------------------------------------------------------------------------
# Lifespan — replaces deprecated @app.on_event
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info(
        "Starting Finance Analytics API",
        extra={"environment": settings.ENVIRONMENT, "version": "2.0.0"},
    )
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created")

    yield  # Application is running

    # --- Shutdown ---
    logger.info("Shutting down Finance Analytics API")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="2.0.0",
        description=(
            "A production-grade Finance Analytics REST API with JWT authentication, "
            "role-based access control, rate limiting, and real-time financial insights."
        ),
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
        # Disable default server header
        openapi_tags=[
            {"name": "auth", "description": "Authentication — login and token management"},
            {"name": "users", "description": "User accounts and profile management"},
            {"name": "transactions", "description": "Financial transaction CRUD"},
            {"name": "analytics", "description": "Financial analytics and reporting (Analyst/Admin)"},
            {"name": "admin", "description": "System administration (Admin only)"},
            {"name": "system", "description": "Health and readiness probes"},
        ],
    )

    # --- Rate limiter state ---
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Security headers (innermost — runs last on response) ---
    application.add_middleware(SecurityHeadersMiddleware)

    # --- CORS ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    # --- Request logging (outermost — runs first on request) ---
    application.add_middleware(RequestLoggingMiddleware)

    # --- Global exception handlers ---
    register_exception_handlers(application)

    # --- API routes ---
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # --- System endpoints ---
    @application.get("/health", tags=["system"], summary="Liveness probe")
    def health_check():
        """Returns 200 if the application process is alive."""
        return {"status": "ok", "service": settings.PROJECT_NAME, "version": "2.0.0"}

    @application.get("/ready", tags=["system"], summary="Readiness probe")
    def readiness_check():
        """Returns 200 if the app can serve traffic (checks DB connectivity)."""
        from sqlalchemy import text
        from app.core.database import SessionLocal
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "ready", "database": "connected"}
        except Exception as e:
            logger.error("Readiness check failed", exc_info=e)
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Database unavailable")

    return application


app = create_app()
