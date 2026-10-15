from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models.user import User
from pydantic import BaseModel, Field
from app.schemas.control_plan import (
    ControlPlanCreate,
    ControlPlanRead,
    ControlPlanItemRead,
    ControlPlanItemUpdate,
)
from app.services.control_plan_service import (
    get_control_plan_by_pfmea,
    create_control_plan_from_pfmea,
    sync_critical_items,
    update_control_plan_item,
)


class ControlPlanPage(BaseModel):
    items: list[ControlPlanRead]
    total: int
    skip: int
    limit: int


class ControlPlanTransition(BaseModel):
    new_status: str = Field(pattern=r"^(Draft|In Review|Approved|Archived)$")


router = APIRouter(prefix="/control-plans", tags=["Control Plan"])


@router.get("/project/{pfmea_id}", response_model=ControlPlanRead)
async def get_control_plan(
    pfmea_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener el Plan de Control asociado a un proyecto PFMEA."""
    cp = await get_control_plan_by_pfmea(db, pfmea_id)
    if not cp:
        raise HTTPException(
            status_code=404, detail="Control Plan not found for this PFMEA"
        )
    return cp


@router.post(
    "/project/{pfmea_id}",
    response_model=ControlPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_control_plan(
    pfmea_id: int,
    payload: ControlPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear/generar encabezado de Plan de Control desde un PFMEA."""
    return await create_control_plan_from_pfmea(db, pfmea_id, current_user.id, payload)


@router.post("/{control_plan_id}/sync-from-pfmea", response_model=ControlPlanRead)
async def sync_control_plan(
    control_plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sincronización bajo demanda de causas críticas (AP='H' o S>=9) como ítems de CP."""
    await sync_critical_items(db, control_plan_id, current_user.id)
    # Return updated CP
    from app.services.control_plan_service import _get_control_plan_or_404

    return await _get_control_plan_or_404(db, control_plan_id)


@router.put("/items/{item_id}", response_model=ControlPlanItemRead)
async def update_item(
    item_id: int,
    payload: ControlPlanItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Actualizar especificación, método de medición, etc."""
    return await update_control_plan_item(db, item_id, payload, current_user.id)


@router.get("/", response_model=ControlPlanPage)
async def list_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    customers: str | None = None,
    sort: str = "date-desc",
    db: AsyncSession = Depends(get_db),
):
    from app.services.control_plan_service import list_control_plans

    return await list_control_plans(
        db, skip, limit, search, status_filter, customers, sort
    )


@router.patch("/{control_plan_id}/status", response_model=ControlPlanRead)
async def transition(
    control_plan_id: int,
    payload: ControlPlanTransition,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.services.control_plan_service import transition_control_plan

    return await transition_control_plan(
        db, control_plan_id, payload.new_status, current_user.id
    )


class SourceReview(BaseModel):
    keep: bool
    reason: str = Field(min_length=5, max_length=2000)


@router.post("/items/{item_id}/review-source", response_model=ControlPlanItemRead)
async def review_source(
    item_id: int,
    payload: SourceReview,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.services.control_plan_service import review_source

    return await review_source(
        db, item_id, payload.keep, payload.reason, current_user.id
    )


class ReopenPlan(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


@router.post("/{control_plan_id}/restore", response_model=ControlPlanRead)
async def reopen(
    control_plan_id: int,
    payload: ReopenPlan,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.services.control_plan_service import reopen_control_plan

    return await reopen_control_plan(
        db, control_plan_id, payload.reason, current_user.id
    )
