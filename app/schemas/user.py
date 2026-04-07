from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import RoleEnum


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=150)
    is_active: Optional[bool] = True


# ---------------------------------------------------------------------------
# Create (public signup)
# ---------------------------------------------------------------------------

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Minimum 8 characters")

    # SECURITY: Public signup always creates a viewer.
    # Admins must use the admin endpoint to change roles.
    # Setting `role` here is intentionally not exposed.

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if v.isdigit():
            raise ValueError("Password cannot be entirely numeric.")
        return v


# ---------------------------------------------------------------------------
# Admin creates user with explicit role
# ---------------------------------------------------------------------------

class UserCreateAdmin(UserBase):
    """Used by admins to create users with any role."""
    password: str = Field(..., min_length=8)
    role: RoleEnum = RoleEnum.viewer

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


# ---------------------------------------------------------------------------
# Update (authenticated user updates own profile)
# ---------------------------------------------------------------------------

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


# ---------------------------------------------------------------------------
# Admin update (can change role and active status)
# ---------------------------------------------------------------------------

class UserAdminUpdate(UserUpdate):
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Database & Response schemas
# ---------------------------------------------------------------------------

class UserInDBBase(UserBase):
    id: int
    role: RoleEnum
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserResponse(UserInDBBase):
    """Safe schema returned to clients — no password hash."""
    pass
