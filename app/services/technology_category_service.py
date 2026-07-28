from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technology_category import TechnologyCategory
from app.schemas.technology_category import TechnologyCategoryCreate, TechnologyCategoryUpdate


async def list_categories(
    db: AsyncSession, skip: int = 0, limit: int = 50, q: Optional[str] = None
) -> List[TechnologyCategory]:
    """Retrieve technology categories."""
    stmt = select(TechnologyCategory).order_by(TechnologyCategory.name)

    if q:
        stmt = stmt.where(TechnologyCategory.name.ilike(f"%{q}%"))

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_category(
    db: AsyncSession, payload: TechnologyCategoryCreate
) -> TechnologyCategory:
    """Create a new technology category."""
    # Check if name already exists
    stmt = select(TechnologyCategory).where(TechnologyCategory.name == payload.name)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )

    db_obj = TechnologyCategory(**payload.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_category(
    db: AsyncSession, category_id: int, payload: TechnologyCategoryUpdate
) -> TechnologyCategory:
    """Update an existing technology category."""
    stmt = select(TechnologyCategory).where(TechnologyCategory.id == category_id)
    result = await db.execute(stmt)
    db_obj = result.scalars().first()

    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology category not found",
        )

    # If updating name, check for uniqueness
    if payload.name and payload.name != db_obj.name:
        check_stmt = select(TechnologyCategory).where(TechnologyCategory.name == payload.name)
        check_result = await db.execute(check_stmt)
        if check_result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_category(db: AsyncSession, category_id: int) -> None:
    """Delete a technology category."""
    stmt = select(TechnologyCategory).where(TechnologyCategory.id == category_id)
    result = await db.execute(stmt)
    db_obj = result.scalars().first()

    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology category not found",
        )

    await db.delete(db_obj)
    await db.commit()
