from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.production_line import ProductionLineCreate, ProductionLineRead, ProductionLineListRead, ProductionLineUpdate
from app.services import production_line_service
from app.api.deps import RoleChecker

router = APIRouter(prefix="/production-lines", tags=["Production Lines"])


@router.get("/", response_model=List[ProductionLineListRead])
async def list_production_lines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await production_line_service.list_production_lines(
        db, skip=skip, limit=limit, active_only=active_only
    )


@router.get("/{line_id}", response_model=ProductionLineRead)
async def get_production_line(
    line_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await production_line_service.get_production_line(db, line_id)


@router.post("/", response_model=ProductionLineRead, status_code=status.HTTP_201_CREATED)
async def create_production_line(
    payload: ProductionLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await production_line_service.create_production_line(db, payload)


@router.put("/{line_id}", response_model=ProductionLineRead)
async def update_production_line(
    line_id: int,
    payload: ProductionLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await production_line_service.update_production_line(db, line_id, payload)


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_production_line(
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator'])),
):
    await production_line_service.delete_production_line(db, line_id)
