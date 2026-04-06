from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password

class AuthService:
    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
