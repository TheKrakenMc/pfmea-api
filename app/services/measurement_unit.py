from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.measurement_unit import MeasurementUnit
from app.schemas.measurement_unit import MeasurementUnitCreate, MeasurementUnitUpdate


class MeasurementUnitService:
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[MeasurementUnit]:
        stmt = select(MeasurementUnit).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get(self, db: AsyncSession, id: int) -> Optional[MeasurementUnit]:
        stmt = select(MeasurementUnit).where(MeasurementUnit.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, db: AsyncSession, *, obj_in: MeasurementUnitCreate
    ) -> MeasurementUnit:
        db_obj = MeasurementUnit(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: MeasurementUnit,
        obj_in: Union[MeasurementUnitUpdate, Dict[str, Any]]
    ) -> MeasurementUnit:
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> MeasurementUnit:
        stmt = select(MeasurementUnit).where(MeasurementUnit.id == id)
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj


measurement_unit_service = MeasurementUnitService()
