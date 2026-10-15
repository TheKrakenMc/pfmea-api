from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings
import urllib.parse
from fastapi import Request


settings = get_settings()


def _get_search_path(url: str) -> str:
    if "search_path=" in url:
        decoded_url = urllib.parse.unquote(url)
        parts = decoded_url.split("search_path=")
        if len(parts) > 1:
            val = parts[1]
            for char in ["&", " ", ";", '"', "'"]:
                val = val.split(char)[0]
            if val:
                return f"{val}, public"
    return "pfmea, public"


search_path = _get_search_path(settings.DATABASE_URL)

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    hide_parameters=True,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {"search_path": search_path},
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db(request: Request = None) -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            if request is not None:
                request.state.db = session
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
