"""Minimal FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.db import engine
from app.models.base import Base

# Ensure every model is registered on Base.metadata
import app.models  # noqa: F401

# Routers
from app.api.v1.endpoints.flowchart import router as flowchart_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create tables on startup (dev only). Replace with Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# ── API v1 routes ──────────────────────────────────────────────────────────
app.include_router(flowchart_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
