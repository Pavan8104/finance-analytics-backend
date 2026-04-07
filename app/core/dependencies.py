"""
FastAPI dependency functions for authentication and authorization.

HTTP Status Code convention (RFC 7235 / RFC 6750):
  - 401 Unauthorized → credentials missing or invalid (challenge the client)
  - 403 Forbidden    → credentials valid but insufficient privilege
"""
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, RoleEnum
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


# ---------------------------------------------------------------------------
# Core: decode token and load user
# ---------------------------------------------------------------------------

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Validates the JWT bearer token and returns the authenticated user.
    Raises HTTP 401 on any token problem (missing/expired/malformed).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exception
        # Reject refresh tokens used on protected routes
        if token_data.type != "access":
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception

    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User belonging to this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )
    return user


# ---------------------------------------------------------------------------
# RBAC: role-based access factories
# ---------------------------------------------------------------------------

def require_roles(*allowed_roles: RoleEnum):
    """
    Factory that returns a FastAPI dependency enforcing role-based access.

    Usage:
        current_user: User = Depends(require_roles(RoleEnum.admin, RoleEnum.analyst))
    """
    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{[r.value for r in allowed_roles]}. "
                    f"Your role: {current_user.role.value}."
                ),
            )
        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Convenience dependencies — use these in route definitions
# ---------------------------------------------------------------------------

# Any authenticated user (viewer, analyst, admin)
get_current_active_user = get_current_user

# Analyst or Admin
get_current_active_analyst_or_admin = require_roles(RoleEnum.analyst, RoleEnum.admin)

# Admin only
get_current_active_admin = require_roles(RoleEnum.admin)
