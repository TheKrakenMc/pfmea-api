from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.technology import (
    TechnologyRead,
    TechnologyCreate,
    TechnologyUpdate,
)
from app.schemas.technology_parameter import (
    TechnologyParameterRead,
    TechnologyParameterCreate,
    TechnologyParameterUpdate,
)
from app.services import technology_service
from app.api.deps import RoleChecker, CurrentUser, get_current_user

router = APIRouter(prefix="/technologies", tags=["Technologies"])

# Shared RBAC dependency for write operations
_modifier_roles = RoleChecker(["Administrator", "PFMEA Owner", "Process Engineer"])


# ── Technology CRUD ─────────────────────────────────────────────────────────

@router.get("/", response_model=List[TechnologyRead])
async def list_technologies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List active technologies. All authenticated users can read."""
    return await technology_service.list_technologies(
        db, skip=skip, limit=limit, q=q, category=category
    )


@router.post("/", response_model=TechnologyRead, status_code=status.HTTP_201_CREATED)
async def create_technology(
    payload: TechnologyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Create a new technology."""
    return await technology_service.create_technology(db, payload, current_user.id)


@router.put("/{tech_id}", response_model=TechnologyRead)
async def update_technology(
    tech_id: int,
    payload: TechnologyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Update an existing technology."""
    return await technology_service.update_technology(db, tech_id, payload, current_user.id)


@router.delete("/{tech_id}", response_model=TechnologyRead)
async def delete_technology(
    tech_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Soft delete a technology. Validates dependencies before deleting."""
    return await technology_service.delete_technology(db, tech_id, current_user.id)


@router.get("/{tech_id}/impact")
async def get_technology_impact(
    tech_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get the dependency impact of a technology for deletion warnings."""
    fc_count, prod_count = await technology_service.check_technology_dependencies(db, tech_id)
    return {
        "flowcharts_count": fc_count,
        "products_count": prod_count,
    }


# ── Technology Parameter Sub-resource ───────────────────────────────────────

@router.get("/{tech_id}/parameters", response_model=List[TechnologyParameterRead])
async def list_parameters(
    tech_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List active parameters for a technology."""
    return await technology_service.list_parameters(db, tech_id)


@router.post(
    "/{tech_id}/parameters",
    response_model=TechnologyParameterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_parameter(
    tech_id: int,
    payload: TechnologyParameterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Add a new parameter to a technology."""
    return await technology_service.create_parameter(db, tech_id, payload)


@router.put("/parameters/{param_id}", response_model=TechnologyParameterRead)
async def update_parameter(
    param_id: int,
    payload: TechnologyParameterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Update an existing technology parameter."""
    return await technology_service.update_parameter(db, param_id, payload)


@router.delete("/parameters/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter(
    param_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Soft delete a technology parameter."""
    await technology_service.delete_parameter(db, param_id)

