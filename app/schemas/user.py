from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import RoleEnum

class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str
    role: Optional[RoleEnum] = RoleEnum.viewer

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    role: RoleEnum
    created_at: datetime
    
    model_config = {"from_attributes": True}

class User(UserInDBBase):
    pass
