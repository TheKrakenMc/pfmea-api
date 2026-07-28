from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_family import ProductFamily
from app.schemas.product_family import ProductFamilyCreate, ProductFamilyUpdate


async def list_product_families(db: AsyncSession, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[ProductFamily]:
    stmt = select(ProductFamily)
    if active_only:
        stmt = stmt.where(ProductFamily.is_active == True)
    stmt = stmt.order_by(ProductFamily.name).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product_family(db: AsyncSession, family_id: int) -> ProductFamily:
    family = await db.get(ProductFamily, family_id)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product Family {family_id} not found"
        )
    return family


async def create_product_family(db: AsyncSession, obj_in: ProductFamilyCreate) -> ProductFamily:
    # Check if name already exists
    stmt = select(ProductFamily).where(ProductFamily.name == obj_in.name)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product Family with name '{obj_in.name}' already exists"
        )
        
    db_obj = ProductFamily(**obj_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_product_family(db: AsyncSession, family_id: int, obj_in: ProductFamilyUpdate) -> ProductFamily:
    db_obj = await get_product_family(db, family_id)
    
    update_data = obj_in.model_dump(exclude_unset=True)
    
    # If name is being updated, check for duplicates
    if "name" in update_data and update_data["name"] != db_obj.name:
        stmt = select(ProductFamily).where(ProductFamily.name == update_data["name"])
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product Family with name '{update_data['name']}' already exists"
            )
            
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_product_family(db: AsyncSession, family_id: int) -> None:
    db_obj = await get_product_family(db, family_id)
    # Instead of hard delete, maybe just deactivate if it is used, but for now we delete or deactivate.
    # We will do hard delete for now. If it has FK constraints, it might fail. Let's do soft delete by setting is_active=False
    db_obj.is_active = False
    await db.commit()
