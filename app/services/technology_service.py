from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.technology import Technology

from app.models.flowchart_step import FlowchartStep
from app.models.product_technology import ProductTechnologyMapping
from app.models.plant import Plant
from app.schemas.technology import (
    TechnologyCreate,
    TechnologyUpdate,
)
from app.schemas.technology_parameter import (
    TechnologyParameterCreate,
    TechnologyParameterUpdate,
)
from app.models.technology_parameter import TechnologyParameter


# ── Technology CRUD ─────────────────────────────────────────────────────────

async def list_technologies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Technology]:
    stmt = (
        select(Technology)
        .options(selectinload(Technology.parameters.and_(TechnologyParameter.is_active == True)))
        .where(Technology.is_active == True)
    )

    if q:
        stmt = stmt.where(
            or_(
                Technology.name.ilike(f"%{q}%"),
                Technology.description.ilike(f"%{q}%"),
            )
        )

    if category:
        stmt = stmt.where(Technology.category == category)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_technology(db: AsyncSession, tech_id: int) -> Technology:
    stmt = (
        select(Technology)
        .options(selectinload(Technology.parameters.and_(TechnologyParameter.is_active == True)))
        .where(Technology.id == tech_id, Technology.is_active == True)
    )
    result = await db.execute(stmt)
    tech = result.scalars().first()

    if not tech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology not found",
        )
    return tech


async def create_technology(
    db: AsyncSession,
    payload: TechnologyCreate,
    user_id: int,
) -> Technology:
    data = payload.model_dump(exclude={"plant_ids"})
    data["created_by"] = user_id

    db_tech = Technology(**data)

    if payload.plant_ids:
        stmt = select(Plant).where(Plant.id.in_(payload.plant_ids))
        result = await db.execute(stmt)
        plants = result.scalars().all()
        db_tech.plants = list(plants)

    db.add(db_tech)
    await db.commit()
    await db.refresh(db_tech)
    return db_tech


async def update_technology(
    db: AsyncSession,
    tech_id: int,
    payload: TechnologyUpdate,
    user_id: int,
) -> Technology:
    db_tech = await get_technology(db, tech_id)

    update_data = payload.model_dump(exclude_unset=True, exclude={"plant_ids"})
    for key, value in update_data.items():
        setattr(db_tech, key, value)

    if payload.plant_ids is not None:
        stmt = select(Plant).where(Plant.id.in_(payload.plant_ids))
        result = await db.execute(stmt)
        plants = result.scalars().all()
        db_tech.plants = list(plants)

    db_tech.updated_by = user_id
    await db.commit()
    await db.refresh(db_tech)
    return db_tech


async def check_technology_dependencies(
    db: AsyncSession, tech_id: int
) -> Tuple[int, int]:
    """Returns the count of related active flowchart steps and products."""

    fc_stmt = select(func.count(FlowchartStep.id)).where(
        FlowchartStep.technology_id == tech_id
    )
    fc_result = await db.execute(fc_stmt)
    fc_count = fc_result.scalar_one()

    prod_stmt = select(func.count(ProductTechnologyMapping.id)).where(
        ProductTechnologyMapping.technology_id == tech_id
    )
    prod_result = await db.execute(prod_stmt)
    prod_count = prod_result.scalar_one()

    return fc_count, prod_count


async def delete_technology(
    db: AsyncSession, tech_id: int, user_id: int
) -> None:
    db_tech = await get_technology(db, tech_id)

    fc_count, prod_count = await check_technology_dependencies(db, tech_id)

    if fc_count > 0 or prod_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Cannot delete technology — it is referenced by active resources.",
                "flowcharts_count": fc_count,
                "products_count": prod_count,
            },
        )

    db_tech.is_active = False
    db_tech.updated_by = user_id
    await db.commit()



# ── Technology Parameters CRUD ──────────────────────────────────────────────

async def list_parameters(
    db: AsyncSession, tech_id: int
) -> List[TechnologyParameter]:
    """Return all active parameters for a technology."""
    await get_technology(db, tech_id)

    stmt = (
        select(TechnologyParameter)
        .options(selectinload(TechnologyParameter.measurement_unit))
        .where(
            TechnologyParameter.technology_id == tech_id,
            TechnologyParameter.is_active == True,
        )
        .order_by(TechnologyParameter.id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_parameter(
    db: AsyncSession,
    tech_id: int,
    payload: TechnologyParameterCreate,
) -> TechnologyParameter:
    await get_technology(db, tech_id)

    param = TechnologyParameter(technology_id=tech_id, **payload.model_dump())
    db.add(param)
    await db.commit()
    await db.refresh(param)
    
    # Reload with relationships
    stmt = select(TechnologyParameter).options(selectinload(TechnologyParameter.measurement_unit)).where(TechnologyParameter.id == param.id)
    res = await db.execute(stmt)
    return res.scalars().first()


async def update_parameter(
    db: AsyncSession,
    param_id: int,
    payload: TechnologyParameterUpdate,
) -> TechnologyParameter:
    stmt = select(TechnologyParameter).where(TechnologyParameter.id == param_id)
    result = await db.execute(stmt)
    param = result.scalars().first()

    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology parameter not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(param, key, value)

    await db.commit()
    
    # Reload with relationships
    stmt = select(TechnologyParameter).options(selectinload(TechnologyParameter.measurement_unit)).where(TechnologyParameter.id == param.id)
    res = await db.execute(stmt)
    return res.scalars().first()


async def delete_parameter(db: AsyncSession, param_id: int) -> None:
    stmt = select(TechnologyParameter).where(TechnologyParameter.id == param_id)
    result = await db.execute(stmt)
    param = result.scalars().first()

    if not param:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology parameter not found",
        )

    param.is_active = False
    await db.commit()
