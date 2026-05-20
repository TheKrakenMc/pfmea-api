from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Union
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ENVIRONMENT: str = "production"
    
    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = ["*"]
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/pfmea"

    # Async driver override (used at runtime)
    @property
    def async_database_url(self) -> str:
        """Replace sync driver with asyncpg for async sessions."""
        url = self.DATABASE_URL.replace("psycopg2", "asyncpg")
        if "?options=" in url:
            url = url.split("?options=")[0]
        return url

    APP_NAME: str = "PFMEA API"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}
    
    @property
    def get_allowed_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            try:
                # Try parsing as JSON list if it's a string representation of a list
                parsed = json.loads(self.ALLOWED_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # Comma separated fallback
                return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS


@lru_cache
def get_settings() -> Settings:
    return Settings()
