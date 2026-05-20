from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/pfmea"

    # Async driver override (used at runtime)
    @property
    def async_database_url(self) -> str:
        """Replace sync driver with asyncpg for async sessions."""
        return self.DATABASE_URL.replace("psycopg2", "asyncpg")

    APP_NAME: str = "PFMEA API"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
