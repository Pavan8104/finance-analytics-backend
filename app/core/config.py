import secrets
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    PROJECT_NAME: str = "Finance Analytics API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development | staging | production

    # ---------------------------------------------------------------------------
    # Security
    # ---------------------------------------------------------------------------
    # CRITICAL: Must be set via .env in any non-development environment.
    # Generate with: openssl rand -hex 32
    SECRET_KEY: str = secrets.token_hex(32)  # Safe default only for dev
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------------------------------------------------------------------------
    # CORS — Restrict to specific origins in production
    # ---------------------------------------------------------------------------
    # Accepts a JSON array OR a comma-separated string:
    #   CORS_ORIGINS='["http://app.com"]'   (JSON)
    #   CORS_ORIGINS="http://app.com,http://admin.com"  (CSV)
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list]) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try JSON first, fall back to CSV
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ---------------------------------------------------------------------------
    # Rate Limiting
    # ---------------------------------------------------------------------------
    RATE_LIMIT_PER_MINUTE: int = 60

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if v and v.strip():
            return v
        # Fall back to SQLite for local development
        return "sqlite:///./finance.db"

    @model_validator(mode="after")
    def enforce_production_secret(self) -> "Settings":
        """
        In production, reject the auto-generated SECRET_KEY.
        Developers must set a real SECRET_KEY in .env.
        """
        if self.ENVIRONMENT == "production" and len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters in production. "
                "Generate one with: openssl rand -hex 32"
            )
        return self

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
