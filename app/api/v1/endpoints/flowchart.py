from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import limiter
from app.schemas.flowchart import (
    FlowchartCreate,
    FlowchartRead,
    FlowchartStepCreate,
    FlowchartStepRead,
    FlowchartStepsReorder,
)
from app.api.deps import RoleChecker
from app.services import flowchart_service

router = APIRouter(prefix="/flowcharts", tags=["Flowcharts"])


# ---------------------------------------------------------------------------
# Flowchart CRUD
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=FlowchartRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear diagrama de flujo",
    description=(
        "Crea un nuevo diagrama de flujo asociado a un producto. "
        "Opcionalmente puede incluir una lista de pasos en la misma solicitud."
    ),
)
async def create_flowchart(
    payload: FlowchartCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner']))
) -> FlowchartRead:
    flowchart = await flowchart_service.create_flowchart(db, payload)
    return FlowchartRead.model_validate(flowchart)


@router.get(
    "/",
    response_model=List[FlowchartRead],
    summary="Listar diagramas de flujo",
)
async def list_flowcharts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[FlowchartRead]:
    flowcharts = await flowchart_service.list_flowcharts(db, skip=skip, limit=limit)
    return [FlowchartRead.model_validate(fc) for fc in flowcharts]


@router.get(
    "/{flowchart_id}",
    response_model=FlowchartRead,
    summary="Obtener diagrama de flujo con pasos",
    description=(
        "Devuelve el diagrama de flujo completo con sus pasos "
        "cargados de forma eager (joinedload) para evitar N+1."
    ),
)
async def get_flowchart(
    flowchart_id: int,
    db: AsyncSession = Depends(get_db),
) -> FlowchartRead:
    flowchart = await flowchart_service.get_flowchart(db, flowchart_id)
    return FlowchartRead.model_validate(flowchart)


# ---------------------------------------------------------------------------
# Flowchart Steps (nested resource)
# ---------------------------------------------------------------------------

@router.post(
    "/{flowchart_id}/steps",
    response_model=FlowchartStepRead,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar paso al diagrama",
    description=(
        "Inserta un nuevo paso de proceso en el diagrama de flujo indicado. "
        "Valida que el step_number sea único dentro del mismo flowchart."
    ),
)
async def add_step(
    flowchart_id: int,
    payload: FlowchartStepCreate,
    db: AsyncSession = Depends(get_db),
) -> FlowchartStepRead:
    step = await flowchart_service.add_step(db, flowchart_id, payload)
    return FlowchartStepRead.model_validate(step)


@router.put(
    "/{flowchart_id}/steps",
    response_model=FlowchartRead,
    summary="Reordenar / reemplazar pasos del diagrama",
    description=(
        "Reemplaza atómicamente todos los pasos del diagrama de flujo "
        "con el nuevo array ordenado. Usado por el auto-save del frontend "
        "después de eventos de Drag & Drop."
    ),
)
@limiter.limit("10/minute")
async def replace_steps(
    request: Request,
    flowchart_id: int,
    payload: FlowchartStepsReorder,
    db: AsyncSession = Depends(get_db),
) -> FlowchartRead:
    flowchart = await flowchart_service.replace_steps(db, flowchart_id, payload.steps)
    return FlowchartRead.model_validate(flowchart)
