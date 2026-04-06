import secrets
from typing import Any, Dict, Optional, Union
from pydantic import PostgresDsn, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Finance Analytics API"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "d0cd650f90cba72fa23126dd1c3c9e6bbad6e2d93e803c4f74d0db8d64af1a1a" # Generate using `openssl rand -hex 32`
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Environment
    ENVIRONMENT: str = "local" # local, staging, production
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str) and v != "":
            return v
        
        # Fall back to SQLite if PostgreSQL is not specified
        return "sqlite:///./finance.db"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", env_file_encoding="utf-8")

settings = Settings()
