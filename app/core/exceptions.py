"""
Custom exception hierarchy and FastAPI exception handlers.

Design:
- All domain exceptions extend AppException for uniform handling.
- A single global handler converts them to clean JSON responses.
- SQLAlchemy IntegrityError is caught and surfaced as a 409 Conflict.
- Unhandled exceptions return a generic 500 without leaking internals.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError

from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class AppException(Exception):
    """Base class for all application-level exceptions."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(detail=f"{resource} not found.", status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppException):
    def __init__(self, detail: str = "A conflict occurred with existing data."):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Authentication credentials were not provided or are invalid."):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ValidationError(AppException):
    def __init__(self, detail: str = "Invalid input data."):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


# ---------------------------------------------------------------------------
# Helper to build a consistent error response body
# ---------------------------------------------------------------------------

def _error_body(status_code: int, detail: str, error_type: str = "error") -> dict:
    return {
        "error": error_type,
        "detail": detail,
        "status_code": status_code,
    }


# ---------------------------------------------------------------------------
# Exception handlers — register all on the FastAPI app
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application exception",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.status_code, exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Surface the first validation error in a human-readable way
        errors = exc.errors()
        detail = "; ".join(
            f"{' -> '.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in errors
        )
        logger.warning("Request validation failed", extra={"detail": detail, "path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(422, detail, "validation_error"),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.error("Database integrity error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body(409, "A record with this data already exists.", "conflict"),
        )

    @app.exception_handler(OperationalError)
    async def db_operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
        logger.error("Database operational error", exc_info=exc, extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body(503, "Database is temporarily unavailable.", "db_error"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={"path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(500, "An unexpected internal server error occurred.", "internal_error"),
        )
