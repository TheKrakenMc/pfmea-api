"""Minimal FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.db import engine
from app.models.base import Base # reload trigger 3

# Ensure every model is registered on Base.metadata
import app.models  # noqa: F401

# Routers


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create tables on startup (dev only). Replace with Alembic in production."""
    # 1. Run database migrations dynamically
    try:
        from run_migrations import main as run_db_migrations
        print("🚀 [STARTUP] Running database migrations...")
        run_db_migrations()
        print("✅ [STARTUP] Database migrations successfully checked/applied.")
    except Exception as e:
        print(f"❌ [STARTUP ERROR] Database migration failed: {e}")
        
    # 2. Run defensive seeding (Roles, default Plant/Region, and Admin user)
    try:
        from app.services.seed import seed_admin_user
        print("🚀 [STARTUP] Seeding administrative account...")
        await seed_admin_user()
        print("✅ [STARTUP] Seeding completed.")
    except Exception as e:
        print(f"❌ [STARTUP ERROR] Administrative seeding failed: {e}")
        
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

# Add Audit Log Middleware
from app.middleware.audit import AuditLogMiddleware
app.add_middleware(AuditLogMiddleware)

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
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.flowchart import router as flowchart_router
from app.api.v1.endpoints.document_version import router as document_version_router
from app.api.v1.endpoints.pfmea_project import router as pfmea_project_router
from app.api.v1.endpoints.control_plan import router as control_plan_router
from app.api.v1.endpoints.instruction import router as instruction_router
from app.api.v1.endpoints.audit_log import router as audit_log_router
from app.api.v1.endpoints.process_analysis import router as process_analysis_router
from app.api.v1.endpoints.product import router as product_router
from app.api.v1.endpoints.technology import router as technology_router
from app.api.v1.endpoints.customers import router as customers_router
from app.api.v1.endpoints.machinery import router as machinery_router
from app.api.v1.endpoints.plants import router as plants_router
from app.api.v1.endpoints.manufacturing_locations import router as manufacturing_locations_router
from app.api.v1.endpoints.product_families import router as product_families_router
from app.api.v1.endpoints.production_lines import router as production_lines_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.technology_categories import router as technology_categories_router
from app.api.v1.endpoints.measurement_units import router as measurement_units_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(flowchart_router, prefix="/api/v1")
app.include_router(document_version_router, prefix="/api/v1")
app.include_router(pfmea_project_router, prefix="/api/v1")
app.include_router(control_plan_router, prefix="/api/v1")
app.include_router(instruction_router, prefix="/api/v1")
app.include_router(audit_log_router, prefix="/api/v1")
app.include_router(process_analysis_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")
app.include_router(technology_router, prefix="/api/v1")
app.include_router(technology_categories_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(machinery_router, prefix="/api/v1/machinery", tags=["machinery"])
app.include_router(plants_router, prefix="/api/v1/plants", tags=["plants"])
app.include_router(manufacturing_locations_router, prefix="/api/v1")
app.include_router(product_families_router, prefix="/api/v1")
app.include_router(production_lines_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1/departments", tags=["departments"])
app.include_router(measurement_units_router, prefix="/api/v1/measurement-units", tags=["measurement_units"])


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/v1/migrate_now")
def migrate_now():
    import os
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("DATABASE_URL").replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE pfmea.products ADD COLUMN IF NOT EXISTS dimensions VARCHAR;
        ALTER TABLE pfmea.products ADD COLUMN IF NOT EXISTS weight DOUBLE PRECISION;
        ALTER TABLE pfmea.products ADD COLUMN IF NOT EXISTS cycle_time DOUBLE PRECISION;
        ALTER TABLE pfmea.products ADD COLUMN IF NOT EXISTS rate_per_hour DOUBLE PRECISION;
    """)
    return {"status": "migrated"}
