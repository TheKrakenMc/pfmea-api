from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.schemas.measurement_unit import MeasurementUnit, MeasurementUnitCreate, MeasurementUnitUpdate
from app.services.measurement_unit import measurement_unit_service

router = APIRouter()


@router.get("/", response_model=List[MeasurementUnit])
async def read_measurement_units(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve measurement units.
    """
    return await measurement_unit_service.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=MeasurementUnit)
async def create_measurement_unit(
    *,
    db: AsyncSession = Depends(get_db),
    unit_in: MeasurementUnitCreate,
) -> Any:
    """
    Create new measurement unit.
    """
    return await measurement_unit_service.create(db, obj_in=unit_in)


@router.get("/{id}", response_model=MeasurementUnit)
async def read_measurement_unit(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
) -> Any:
    """
    Get measurement unit by ID.
    """
    unit = await measurement_unit_service.get(db, id=id)
    if not unit:
        raise HTTPException(status_code=404, detail="Measurement unit not found")
    return unit


@router.put("/{id}", response_model=MeasurementUnit)
async def update_measurement_unit(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    unit_in: MeasurementUnitUpdate,
) -> Any:
    """
    Update a measurement unit.
    """
    unit = await measurement_unit_service.get(db, id=id)
    if not unit:
        raise HTTPException(status_code=404, detail="Measurement unit not found")
    unit = await measurement_unit_service.update(db, db_obj=unit, obj_in=unit_in)
    return unit


@router.delete("/{id}", response_model=MeasurementUnit)
async def delete_measurement_unit(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
) -> Any:
    """
    Delete a measurement unit.
    """
    unit = await measurement_unit_service.get(db, id=id)
    if not unit:
        raise HTTPException(status_code=404, detail="Measurement unit not found")
    unit = await measurement_unit_service.remove(db, id=id)
    return unit
