from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.machinery import Machinery
from app.schemas.machinery import MachineryCreate, MachineryUpdate

class MachineryService:
    @staticmethod
    async def get_multi(
        db: AsyncSession, *, skip: int = 0, limit: int = 100, q: Optional[str] = None, plant_id: Optional[int] = None, is_active: Optional[bool] = None
    ) -> List[Machinery]:
        stmt = select(Machinery)
        if q:
            stmt = stmt.where(or_(Machinery.machinery_name.ilike(f"%{q}%"), Machinery.machinery_code.ilike(f"%{q}%")))
        if plant_id is not None:
            stmt = stmt.where(Machinery.plant_id == plant_id)
        if is_active is not None:
            stmt = stmt.where(Machinery.is_active == is_active)
        
        stmt = stmt.offset(skip).limit(limit)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def get(db: AsyncSession, id: int) -> Optional[Machinery]:
        stmt = select(Machinery).where(Machinery.id == id)
        res = await db.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def create(db: AsyncSession, *, obj_in: MachineryCreate) -> Machinery:
        db_obj = Machinery(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update(db: AsyncSession, *, db_obj: Machinery, obj_in: MachineryUpdate) -> Machinery:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def remove(db: AsyncSession, *, id: int) -> Machinery:
        stmt = select(Machinery).where(Machinery.id == id)
        res = await db.execute(stmt)
        db_obj = res.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

machinery_service = MachineryService()
