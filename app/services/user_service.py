from datetime import datetime, timezone
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserAdminUpdate
from app.core.security import get_password_hash, verify_password


class UserService:

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_multi(
        db: Session, *, skip: int = 0, limit: int = 100
    ) -> Tuple[List[User], int]:
        total = db.query(User).count()
        users = db.query(User).offset(skip).limit(limit).all()
        return users, total

    @staticmethod
    def create(db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user from a public signup.
        Role is always forced to 'viewer' to prevent privilege escalation.
        """
        from app.models.user import RoleEnum
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password),
            role=RoleEnum.viewer,   # SECURITY: never trust client-supplied role
            is_active=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def create_admin(db: Session, *, obj_in) -> User:
        """Create a user with an explicit role — admin-only operation."""
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=get_password_hash(obj_in.password),
            role=obj_in.role,
            is_active=obj_in.is_active if obj_in.is_active is not None else True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_last_login(db: Session, *, user: User) -> User:
        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def remove(db: Session, *, id: int) -> Optional[User]:
        obj = db.query(User).filter(User.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj
