from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production_line import ProductionLine
from app.schemas.production_line import ProductionLineCreate, ProductionLineUpdate


async def list_production_lines(db: AsyncSession, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[ProductionLine]:
    stmt = select(ProductionLine)
    if active_only:
        stmt = stmt.where(ProductionLine.is_active == True)
    stmt = stmt.order_by(ProductionLine.name).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_production_line(db: AsyncSession, line_id: int) -> ProductionLine:
    line = await db.get(ProductionLine, line_id)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production Line {line_id} not found"
        )
    return line


async def create_production_line(db: AsyncSession, obj_in: ProductionLineCreate) -> ProductionLine:
    # Check if name already exists
    stmt = select(ProductionLine).where(ProductionLine.name == obj_in.name)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Production Line with name '{obj_in.name}' already exists"
        )
        
    db_obj = ProductionLine(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_production_line(db: AsyncSession, line_id: int, obj_in: ProductionLineUpdate) -> ProductionLine:
    db_obj = await get_production_line(db, line_id)
    
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # If name is being updated, check for duplicates
    if "name" in update_data and update_data["name"] != db_obj.name:
        stmt = select(ProductionLine).where(ProductionLine.name == update_data["name"])
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Production Line with name '{update_data['name']}' already exists"
            )
            
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_production_line(db: AsyncSession, line_id: int) -> None:
    db_obj = await get_production_line(db, line_id)
    # Hard delete might fail due to FK constraints. Let's do hard delete for now, or soft delete if preferred.
    # We will do hard delete to match the delete endpoint expectation, or soft delete by setting is_active=False
    # Note: frontend UI often expects true deletion unless backend hides it. Let's do hard delete and catch FK error.
    try:
        await db.delete(db_obj)
        await db.commit()
    except Exception as e:
        # Fallback to soft delete
        db_obj.is_active = False
        await db.commit()
