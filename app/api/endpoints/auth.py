"""
Authentication endpoints with rate limiting.

Login is limited to 10 attempts per minute per IP to mitigate brute-force attacks.
"""
import os
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.token import Token, TokenWithRefresh
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.logger import logger

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/login",
    response_model=TokenWithRefresh,
    summary="Login with email and password",
    description=(
        "OAuth2-compatible login. Returns an **access token** (30 min TTL) "
        "and a **refresh token** (7 day TTL). "
        "Rate limited to **10 requests per minute** per IP."
    ),
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Account deactivated"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute", exempt_when=lambda: os.getenv("ENVIRONMENT") == "test")
def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    Rate-limited login endpoint.
    Returns access + refresh JWT tokens on success.
    """
    user = AuthService.authenticate(db, email=form_data.username, password=form_data.password)

    if not user:
        logger.warning(
            "Failed login attempt",
            extra={"email": form_data.username, "ip": request.client.host if request.client else "unknown"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact an administrator.",
        )

    # Record last login timestamp
    UserService.update_last_login(db, user=user)

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"role": user.role.value, "email": user.email},
    )
    refresh_token = create_refresh_token(subject=user.id)

    logger.info(
        "User login successful",
        extra={"user_id": user.id, "role": user.role.value},
    )

    return TokenWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
