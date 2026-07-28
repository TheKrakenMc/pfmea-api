from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.manufacturing_location import ManufacturingLocationCreate, ManufacturingLocationRead, ManufacturingLocationUpdate
from app.services import manufacturing_location_service
from app.api.deps import RoleChecker

router = APIRouter(prefix="/manufacturing_locations", tags=["Manufacturing Locations"])

@router.get("/", response_model=List[ManufacturingLocationRead])
async def list_manufacturing_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = None,
    plant_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await manufacturing_location_service.list_manufacturing_locations(
        db, skip=skip, limit=limit, q=q, plant_id=plant_id
    )

@router.get("/{location_id}", response_model=ManufacturingLocationRead)
async def get_manufacturing_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await manufacturing_location_service.get_manufacturing_location(db, location_id)

@router.post("/", response_model=ManufacturingLocationRead, status_code=status.HTTP_201_CREATED)
async def create_manufacturing_location(
    payload: ManufacturingLocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await manufacturing_location_service.create_manufacturing_location(db, payload)

@router.put("/{location_id}", response_model=ManufacturingLocationRead)
async def update_manufacturing_location(
    location_id: int,
    payload: ManufacturingLocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await manufacturing_location_service.update_manufacturing_location(db, location_id, payload)

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manufacturing_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['Administrator'])),
):
    await manufacturing_location_service.delete_manufacturing_location(db, location_id)
