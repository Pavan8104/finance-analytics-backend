from typing import Optional
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """Payload decoded from a JWT token."""
    sub: Optional[str] = None
    type: str = "access"   # "access" or "refresh"


class Token(BaseModel):
    """Response body returned after a successful login."""
    access_token: str
    token_type: str = "bearer"


class TokenWithRefresh(Token):
    """Extended token response that also includes a refresh token."""
    refresh_token: str
