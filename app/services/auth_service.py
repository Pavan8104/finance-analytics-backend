from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password


class AuthService:

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """
        Verify email + password combination.

        Always calls verify_password even if user doesn't exist to
        prevent timing-based user enumeration attacks.
        """
        user = db.query(User).filter(User.email == email).first()

        # Even if user is None, run verify_password with a dummy hash
        # so the response time is consistent (timing attack prevention)
        dummy_hash = "$2b$12$KIXkJ5hE7pXtZX6wP5i0dOcS4FcKj/JYiL0t4TyFXB7ZDlHCKjVbq"
        target_hash = user.hashed_password if user else dummy_hash

        password_valid = verify_password(password, target_hash)

        if not user or not password_valid:
            return None

        return user
