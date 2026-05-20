"""Service layer for Flowchart & FlowchartStep business logic.

All database interactions for the *Structure Analysis* module
(AIAG-VDA Step 2) live here, keeping routers thin.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.flowchart import Flowchart
from app.models.flowchart_step import FlowchartStep
from app.models.product import Product
from app.models.technology import Technology
from app.schemas.flowchart import FlowchartCreate, FlowchartStepCreate


# ---------------------------------------------------------------------------
# Helpers – existence guards
# ---------------------------------------------------------------------------

async def _ensure_product_exists(db: AsyncSession, product_id: int) -> None:
    """Raise 404 if the referenced product does not exist."""
    result = await db.execute(select(Product.id).where(Product.id == product_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con id {product_id} no encontrado.",
        )


async def _ensure_technology_exists(db: AsyncSession, technology_id: int) -> None:
    """Raise 404 if the referenced technology does not exist."""
    result = await db.execute(
        select(Technology.id).where(Technology.id == technology_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tecnología con id {technology_id} no encontrada.",
        )


async def _ensure_flowchart_exists(
    db: AsyncSession, flowchart_id: int
) -> Flowchart:
    """Return the flowchart or raise 404."""
    result = await db.execute(
        select(Flowchart)
        .options(joinedload(Flowchart.steps))
        .where(Flowchart.id == flowchart_id)
    )
    flowchart = result.unique().scalar_one_or_none()
    if flowchart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagrama de flujo con id {flowchart_id} no encontrado.",
        )
    return flowchart


# ---------------------------------------------------------------------------
# Flowchart CRUD
# ---------------------------------------------------------------------------

async def create_flowchart(
    db: AsyncSession,
    payload: FlowchartCreate,
) -> Flowchart:
    """Create a flowchart with optional inline steps.

    Validates:
    - ``product_id`` exists.
    - Every ``technology_id`` referenced in steps exists.
    - ``step_number`` values are unique within the batch.
    """
    # 1) Validate FK references
    await _ensure_product_exists(db, payload.product_id)

    # 2) Validate step-number uniqueness within the request payload
    step_numbers = [s.step_number for s in payload.steps]
    if len(step_numbers) != len(set(step_numbers)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Números de paso duplicados en la solicitud.",
        )

    # 3) Validate every referenced technology
    for step_data in payload.steps:
        if step_data.technology_id is not None:
            await _ensure_technology_exists(db, step_data.technology_id)

    # 4) Build the ORM graph
    flowchart = Flowchart(
        product_id=payload.product_id,
        owner_id=payload.owner_id,
        title=payload.title,
        status=payload.status,
    )
    for step_data in payload.steps:
        flowchart.steps.append(
            FlowchartStep(
                technology_id=step_data.technology_id,
                step_number=step_data.step_number,
                custom_description=step_data.custom_description,
            )
        )

    db.add(flowchart)
    await db.flush()          # assign PKs without committing
    await db.refresh(flowchart)
    return flowchart


async def get_flowchart(db: AsyncSession, flowchart_id: int) -> Flowchart:
    """Retrieve a flowchart with its steps eagerly loaded (joinedload)."""
    return await _ensure_flowchart_exists(db, flowchart_id)


async def list_flowcharts(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[Flowchart]:
    """Return a paginated list of flowcharts (without steps)."""
    result = await db.execute(
        select(Flowchart)
        .order_by(Flowchart.id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# FlowchartStep management
# ---------------------------------------------------------------------------

async def add_step(
    db: AsyncSession,
    flowchart_id: int,
    payload: FlowchartStepCreate,
) -> FlowchartStep:
    """Add a single step to an existing flowchart.

    Validates:
    - ``flowchart_id`` exists.
    - ``technology_id`` exists (if provided).
    - ``step_number`` is unique within the flowchart
      (enforced at the DB level via unique constraint).
    """
    # 1) Validate parent flowchart
    await _ensure_flowchart_exists(db, flowchart_id)

    # 2) Validate technology FK
    if payload.technology_id is not None:
        await _ensure_technology_exists(db, payload.technology_id)

    # 3) Check step_number uniqueness proactively (better UX than raw DB error)
    existing = await db.execute(
        select(FlowchartStep.id).where(
            FlowchartStep.flowchart_id == flowchart_id,
            FlowchartStep.step_number == payload.step_number,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El paso número {payload.step_number} ya existe "
                f"en el diagrama de flujo {flowchart_id}."
            ),
        )

    # 4) Persist
    step = FlowchartStep(
        flowchart_id=flowchart_id,
        technology_id=payload.technology_id,
        step_number=payload.step_number,
        custom_description=payload.custom_description,
    )
    db.add(step)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Conflicto de integridad al insertar el paso "
                f"{payload.step_number} en el flujo {flowchart_id}."
            ),
        )

    await db.refresh(step)
    return step
