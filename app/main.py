"""Minimal FastAPI application entry point."""

import sys
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import get_settings
from app.core.db import engine
import app.models  # noqa: F401
from app.core.security import limiter
from app.core.security import SecurityHeadersMiddleware
from app.middleware.csrf import OriginMiddleware
from fastapi.middleware.cors import CORSMiddleware
from app.core import data_scope as data_scope, transaction_audit as transaction_audit
from app.api.access import authorize_request
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.flowchart import router as flowchart_router
from app.api.v1.endpoints.document_version import router as document_version_router
from app.api.v1.endpoints.pfmea_project import router as pfmea_project_router
from app.api.v1.endpoints.control_plan import router as control_plan_router
from app.api.v1.endpoints.product import router as product_router
from app.api.v1.endpoints.technology import router as technology_router
from app.api.v1.endpoints.customers import router as customers_router
from app.api.v1.endpoints.machinery import router as machinery_router
from app.api.v1.endpoints.plants import router as plants_router
from app.api.v1.endpoints.manufacturing_locations import (
    router as manufacturing_locations_router,
)
from app.api.v1.endpoints.product_families import router as product_families_router
from app.api.v1.endpoints.production_lines import router as production_lines_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.technology_categories import (
    router as technology_categories_router,
)
from app.api.v1.endpoints.measurement_units import router as measurement_units_router


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


# Ensure every model is registered on Base.metadata

# Routers


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create tables on startup (dev only). Replace with Alembic in production."""
    # Schema migration and administrator provisioning are explicit deployment steps.
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# Add Rate Limiting

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add Security Headers Middleware

app.add_middleware(SecurityHeadersMiddleware)

# Add Audit Log Middleware

app.add_middleware(OriginMiddleware)

# Add CORS Middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Document-Key", "X-Document-Version"],
)


# ── API v1 routes ──────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=[Depends(authorize_request)],
)
app.include_router(
    flowchart_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    document_version_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    pfmea_project_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    control_plan_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
# Provisional module is not exposed.
# Provisional module is not exposed.
# Provisional module is not exposed.
app.include_router(
    product_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    technology_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    technology_categories_router,
    prefix="/api/v1",
    dependencies=[Depends(authorize_request)],
)
app.include_router(
    customers_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    machinery_router,
    prefix="/api/v1/machinery",
    tags=["machinery"],
    dependencies=[Depends(authorize_request)],
)
app.include_router(
    plants_router,
    prefix="/api/v1/plants",
    tags=["plants"],
    dependencies=[Depends(authorize_request)],
)
app.include_router(
    manufacturing_locations_router,
    prefix="/api/v1",
    dependencies=[Depends(authorize_request)],
)
app.include_router(
    product_families_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    production_lines_router, prefix="/api/v1", dependencies=[Depends(authorize_request)]
)
app.include_router(
    departments_router,
    prefix="/api/v1/departments",
    tags=["departments"],
    dependencies=[Depends(authorize_request)],
)
app.include_router(
    measurement_units_router,
    prefix="/api/v1/measurement-units",
    tags=["measurement_units"],
    dependencies=[Depends(authorize_request)],
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/readiness")
async def readiness():
    from sqlalchemy import text
    from fastapi.responses import JSONResponse

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1 FROM auth_sessions LIMIT 0"))
            await conn.execute(text("SELECT lock_version FROM pfmea_headers LIMIT 0"))
            await conn.execute(
                text("SELECT source_reviewed FROM control_plan_items LIMIT 0")
            )
            await conn.execute(text("SELECT lock_version FROM products LIMIT 0"))
            if settings.ENVIRONMENT.lower() in {"production", "staging", "secure"}:
                privileged = (
                    await conn.execute(
                        text(
                            "SELECT rolsuper OR rolbypassrls OR EXISTS (SELECT 1 FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user) AND relname='pfmea_headers') FROM pg_roles WHERE rolname=current_user"
                        )
                    )
                ).scalar()
                if privileged:
                    raise RuntimeError("Application database role must enforce RLS")
        return {"status": "ready"}
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)


@app.exception_handler(IntegrityError)
async def integrity_conflict(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=409,
        content={
            "detail": "Data conflict: verify references and uniqueness before retrying"
        },
    )
