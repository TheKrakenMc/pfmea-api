from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import List, Union
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ENVIRONMENT: str = "development"

    # CORS & URLs
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []
    FRONTEND_URL: str = "http://localhost:5173"

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/pfmea"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email Configuration (Resend)
    RESEND_API_KEY: str = ""
    SMTP_FROM_EMAIL: str = "onboarding@resend.dev"
    SMTP_FROM_NAME: str = "APG Puebla - Notificaciones de Planta"

    # Async driver override (used at runtime)
    @property
    def async_database_url(self) -> str:
        """Replace sync driver with asyncpg for async sessions."""
        # Clean up quotes or whitespace in case they were accidentally included in the Env Var
        url = self.DATABASE_URL.strip().strip('"').strip("'")

        if not url:
            raise ValueError(
                "DATABASE_URL environment variable is empty or not set properly."
            )

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            raise ValueError("Invalid DATABASE_URL scheme; expected PostgreSQL")

        if "?options=" in url:
            url = url.split("?options=")[0]
        return url

    APP_NAME: str = "PFMEA API"
    DEBUG: bool = False

    @model_validator(mode="after")
    def validate_runtime_security(self):
        if self.ENVIRONMENT.lower() in {"production", "staging", "secure"}:
            if (
                len(self.SECRET_KEY) < 32
                or self.SECRET_KEY == "your-super-secret-key-change-in-production"
            ):
                raise ValueError("A strong SECRET_KEY is required outside development")
            if "*" in self.get_allowed_origins:
                raise ValueError("Wildcard credential origins are not allowed")
        return self

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def get_allowed_origins(self) -> List[str]:
        origins = []
        raw_origins = self.BACKEND_CORS_ORIGINS or self.ALLOWED_ORIGINS
        if isinstance(raw_origins, str):
            try:
                parsed = json.loads(raw_origins)
                if isinstance(parsed, list):
                    origins = parsed
            except json.JSONDecodeError:
                origins = [
                    origin.strip()
                    for origin in raw_origins.split(",")
                    if origin.strip()
                ]
        elif isinstance(raw_origins, list):
            origins = list(raw_origins)
        else:
            origins = [str(raw_origins)]

        # Automatically include equivalent localhost/127.0.0.1 origins for seamless dev experience
        expanded_origins = set(origins)
        for orig in origins:
            if "localhost" in orig:
                expanded_origins.add(orig.replace("localhost", "127.0.0.1"))
            elif "127.0.0.1" in orig:
                expanded_origins.add(orig.replace("127.0.0.1", "localhost"))

        return list(expanded_origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()
