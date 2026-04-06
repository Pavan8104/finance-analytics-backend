from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_service import UserService
from app.core.dependencies import get_current_user, get_current_active_admin
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user. Publicly accessible for signup.
    """
    user = UserService.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = UserService.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=User)
def read_user_me(
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_admin),
) -> Any:
    """
    Retrieve users. Requires admin role.
    """
    users, _ = UserService.get_multi(db, skip=skip, limit=limit)
    return users
