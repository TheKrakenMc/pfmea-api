"""Minimal FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

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

# Add Rate Limiting
from app.core.security import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add Security Headers Middleware
from app.core.security import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

secure_environments = ["production", "staging", "secure"]
is_secure_env = settings.ENVIRONMENT.lower() in secure_environments

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=is_secure_env,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API v1 routes ──────────────────────────────────────────────────────────
from app.api.v1.endpoints.auth import router as auth_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(flowchart_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
