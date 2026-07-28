from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.technology_category import (
    TechnologyCategoryRead,
    TechnologyCategoryCreate,
    TechnologyCategoryUpdate,
)
from app.services import technology_category_service
from app.api.deps import RoleChecker, CurrentUser, get_current_user

router = APIRouter(prefix="/technology-categories", tags=["Technology Categories"])

# Shared RBAC dependency for write operations
_modifier_roles = RoleChecker(["Administrator", "PFMEA Owner", "Process Engineer"])


@router.get("/", response_model=List[TechnologyCategoryRead])
async def list_technology_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List technology categories."""
    return await technology_category_service.list_categories(db, skip=skip, limit=limit, q=q)


@router.post("/", response_model=TechnologyCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_technology_category(
    payload: TechnologyCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Create a new technology category."""
    return await technology_category_service.create_category(db, payload)


@router.put("/{category_id}", response_model=TechnologyCategoryRead)
async def update_technology_category(
    category_id: int,
    payload: TechnologyCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Update an existing technology category."""
    return await technology_category_service.update_category(db, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technology_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(_modifier_roles),
):
    """Delete a technology category."""
    await technology_category_service.delete_category(db, category_id)
