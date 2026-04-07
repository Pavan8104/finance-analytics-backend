from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    get_current_active_user,
    get_current_active_admin,
)
from app.models.user import User as UserModel, RoleEnum
from app.schemas.user import UserCreate, UserCreateAdmin, UserAdminUpdate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.utils.logger import logger

router = APIRouter()


# ---------------------------------------------------------------------------
# Public: Signup
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account (public signup)",
)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Public signup endpoint. Role is always set to `viewer`.
    To create users with elevated roles, an admin must use POST /users/admin.
    """
    existing = UserService.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = UserService.create(db, obj_in=user_in)
    logger.info("New user registered", extra={"user_id": user.id, "email": user.email})
    return user


# ---------------------------------------------------------------------------
# Authenticated: Own profile
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def read_user_me(
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """Returns the profile of the currently authenticated user."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update own profile",
)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Allows the authenticated user to update their own name, email, or password.
    Role and active status are NOT changeable via this endpoint.
    """
    if user_in.email and user_in.email != current_user.email:
        if UserService.get_by_email(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email is already in use.",
            )
    return UserService.update(db, db_obj=current_user, obj_in=user_in)


# ---------------------------------------------------------------------------
# Admin: User management
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users (admin only)",
)
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_admin),
) -> Any:
    """Returns all users. Requires Admin role."""
    users, _ = UserService.get_multi(db, skip=skip, limit=limit)
    return users


@router.post(
    "/admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user with explicit role (admin only)",
)
def admin_create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreateAdmin,
    current_user: UserModel = Depends(get_current_active_admin),
) -> Any:
    """
    Admin-only endpoint to create a user with any role.
    This is the ONLY way to create admin or analyst accounts.
    """
    existing = UserService.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = UserService.create_admin(db, obj_in=user_in)
    logger.info(
        "Admin created user",
        extra={"admin_id": current_user.id, "new_user_id": user.id, "role": user.role.value},
    )
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update any user (admin only)",
)
def admin_update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserAdminUpdate,
    current_user: UserModel = Depends(get_current_active_admin),
) -> Any:
    """Admin-only endpoint to update any user's role, status, or profile."""
    user = UserService.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserService.update(db, db_obj=user, obj_in=user_in)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (admin only)",
)
def admin_delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: UserModel = Depends(get_current_active_admin),
) -> None:
    """Admin-only endpoint to delete a user account."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot delete their own account.",
        )
    user = UserService.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    UserService.remove(db, id=user_id)
