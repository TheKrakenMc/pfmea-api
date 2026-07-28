from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturing_location import ManufacturingLocation
from app.schemas.manufacturing_location import ManufacturingLocationCreate, ManufacturingLocationUpdate

async def list_manufacturing_locations(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    plant_id: Optional[int] = None
) -> List[ManufacturingLocation]:
    stmt = select(ManufacturingLocation).where(ManufacturingLocation.is_active == True)

    if q:
        stmt = stmt.where(
            or_(
                ManufacturingLocation.location_code.ilike(f"%{q}%"),
                ManufacturingLocation.location_name.ilike(f"%{q}%"),
                ManufacturingLocation.location_type.ilike(f"%{q}%")
            )
        )
        
    if plant_id:
        stmt = stmt.where(ManufacturingLocation.plant_id == plant_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_manufacturing_location(db: AsyncSession, location_id: int) -> ManufacturingLocation:
    stmt = select(ManufacturingLocation).where(ManufacturingLocation.id == location_id, ManufacturingLocation.is_active == True)
    
    result = await db.execute(stmt)
    location = result.scalars().first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturing Location not found"
        )
    return location

async def create_manufacturing_location(db: AsyncSession, payload: ManufacturingLocationCreate) -> ManufacturingLocation:
    location_dict = payload.model_dump()
    
    db_location = ManufacturingLocation(**location_dict)
    db.add(db_location)
    await db.flush()
    await db.commit()
    await db.refresh(db_location)
    
    return db_location

async def update_manufacturing_location(db: AsyncSession, location_id: int, payload: ManufacturingLocationUpdate) -> ManufacturingLocation:
    db_location = await get_manufacturing_location(db, location_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
            
    await db.commit()
    await db.refresh(db_location)
    return db_location

async def delete_manufacturing_location(db: AsyncSession, location_id: int) -> None:
    db_location = await get_manufacturing_location(db, location_id)
    db_location.is_active = False
    await db.commit()
