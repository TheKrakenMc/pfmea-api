from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings

import urllib.parse

settings = get_settings()

def _get_search_path(url: str) -> str:
    if "search_path=" in url:
        decoded_url = urllib.parse.unquote(url)
        parts = decoded_url.split("search_path=")
        if len(parts) > 1:
            val = parts[1]
            for char in ["&", " ", ";", "\"", "'"]:
                val = val.split(char)[0]
            if val:
                return f"{val}, public"
    return "pfmea, public"

search_path = _get_search_path(settings.DATABASE_URL)

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": search_path}},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


from fastapi import Request
from sqlalchemy import text

async def get_db(request: Request = None) -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            if request is not None:
                plant_id = request.headers.get("x-plant-id")
                if plant_id:
                    # Validate plant_id is a number to prevent injection, or just let DB fail
                    # Using parameterised queries for SET is not supported, so string formatting is needed.
                    if plant_id.isdigit():
                        await session.execute(text(f"SET LOCAL app.current_plant_id = '{plant_id}';"))
            
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
