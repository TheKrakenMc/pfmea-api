"""PFMEA Project router — async endpoints for AIAG-VDA 2019 Steps 1–6.

Provides CRUD for headers, team management, worksheet editing,
flowchart sync, MOC status transitions, audit trail, AP lookup,
and a My Tasks endpoint.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.api.deps import (
    CurrentUser,
    PfmeaAccessChecker,
    RoleChecker,
    get_current_user,
)
from app.schemas.pfmea import (
    ActionPriorityRequest,
    ActionPriorityResult,
    MocStatusTransition,
    PfmeaHeaderCreate,
    PfmeaHeaderDetailRead,
    PfmeaHeaderRead,
    PfmeaHeaderUpdate,
    PfmeaTaskRead,
    TeamMemberCreate,
    TeamMemberRead,
    WorksheetRowCreate,
    WorksheetRowRead,
    WorksheetRowUpdate,
)
from app.services import pfmea_service
from app.services.notification import send_team_assign_notification_email

router = APIRouter(prefix="/pfmea-project", tags=["PFMEA Project"])


# ============================================================================
# Header CRUD (Step 1)
# ============================================================================

@router.post(
    "/",
    response_model=PfmeaHeaderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create PFMEA analysis",
    description=(
        "Creates a new PFMEA analysis linked to an existing flowchart. "
        "Generates a hierarchical ID automatically. The creator is added "
        "as PFMEA Owner in the core team."
    ),
)
async def create_analysis(
    payload: PfmeaHeaderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(
        RoleChecker(["Administrator", "PFMEA Owner"])
    ),
) -> PfmeaHeaderRead:
    pfmea = await pfmea_service.create_pfmea_analysis(db, payload, current_user.id)
    return PfmeaHeaderRead.model_validate(pfmea)


@router.get(
    "/",
    response_model=List[PfmeaHeaderRead],
    summary="List PFMEA analyses",
    description="Paginated list of all PFMEA analyses with optional filters.",
)
async def list_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    plant_id: Optional[int] = Query(None),
    owner_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> List[PfmeaHeaderRead]:
    analyses = await pfmea_service.list_pfmea_analyses(
        db, skip=skip, limit=limit,
        status_filter=status_filter, plant_id=plant_id, owner_id=owner_id,
    )
    return [PfmeaHeaderRead.model_validate(a) for a in analyses]


@router.get(
    "/my-tasks",
    response_model=List[PfmeaTaskRead],
    summary="My pending tasks",
    description=(
        "Returns all worksheet rows assigned to the current user "
        "with action_status != 'Completed'. Ordered by priority (H first) "
        "and target date."
    ),
)
async def get_my_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> List[PfmeaTaskRead]:
    tasks = await pfmea_service.get_my_tasks(
        db, current_user.id, skip=skip, limit=limit,
    )
    return [PfmeaTaskRead(**t) for t in tasks]


@router.get(
    "/ap-lookup",
    response_model=ActionPriorityResult,
    summary="AP calculation utility",
    description=(
        "Utility endpoint to calculate the Action Priority (H/M/L) "
        "for given Severity, Occurrence, and Detection values per "
        "AIAG-VDA 2019 methodology."
    ),
)
async def ap_lookup(
    severity: int = Query(..., ge=1, le=10),
    occurrence: int = Query(..., ge=1, le=10),
    detection: int = Query(..., ge=1, le=10),
) -> ActionPriorityResult:
    ap = pfmea_service.ap_lookup(severity, occurrence, detection)
    return ActionPriorityResult(
        severity=severity,
        occurrence=occurrence,
        detection=detection,
        action_priority=ap,
    )


@router.get(
    "/{pfmea_id}",
    response_model=PfmeaHeaderDetailRead,
    summary="Get PFMEA analysis detail",
    description="Returns the full PFMEA analysis with team members and worksheet rows.",
)
async def get_analysis(
    pfmea_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=False)),
) -> PfmeaHeaderDetailRead:
    pfmea = await pfmea_service.get_pfmea_analysis(db, pfmea_id)
    return PfmeaHeaderDetailRead.model_validate(pfmea)


@router.put(
    "/{pfmea_id}",
    response_model=PfmeaHeaderRead,
    summary="Update PFMEA header",
    description=(
        "Update Step 1 metadata (project name, customer, etc.). "
        "Blocked if status is Approved or Archived (HTTP 403)."
    ),
)
async def update_analysis(
    pfmea_id: int,
    payload: PfmeaHeaderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
) -> PfmeaHeaderRead:
    pfmea = await pfmea_service.update_pfmea_header(
        db, pfmea_id, payload, current_user.id,
    )
    return PfmeaHeaderRead.model_validate(pfmea)


# ============================================================================
# MOC Status Transitions
# ============================================================================

@router.patch(
    "/{pfmea_id}/status",
    response_model=PfmeaHeaderRead,
    summary="Transition MOC status",
    description=(
        "Changes the PFMEA lifecycle status. Gate rules:\n"
        "- Draft → In Review: all rows must have Steps 3-5 complete.\n"
        "- In Review → Approved: BLOCKS if any row has AP=H unresolved.\n"
        "- Approved → Archived: terminal transition."
    ),
)
async def transition_status(
    pfmea_id: int,
    payload: MocStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(
        RoleChecker(["Administrator", "PFMEA Owner"])
    ),
) -> PfmeaHeaderRead:
    pfmea = await pfmea_service.transition_moc_status(
        db, pfmea_id, payload.new_status, current_user.id,
    )
    return PfmeaHeaderRead.model_validate(pfmea)


@router.post(
    "/{pfmea_id}/restore",
    response_model=PfmeaHeaderRead,
    summary="Restore to Draft (Admin only)",
    description="Restore an Approved or Archived PFMEA back to Draft, incrementing the version.",
)
async def restore_to_draft(
    pfmea_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(RoleChecker(["Administrator"])),
) -> PfmeaHeaderRead:
    pfmea = await pfmea_service.restore_to_draft(db, pfmea_id, current_user.id)
    return PfmeaHeaderRead.model_validate(pfmea)


# ============================================================================
# Flowchart Sync
# ============================================================================

@router.post(
    "/{pfmea_id}/sync-flowchart",
    response_model=List[WorksheetRowRead],
    summary="Sync worksheet from flowchart",
    description=(
        "Populates/updates worksheet rows from the linked flowchart steps. "
        "Creates one row per step that doesn't already have a mapping. "
        "Existing rows are updated with fresh structure-analysis data."
    ),
)
async def sync_flowchart(
    pfmea_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
) -> List[WorksheetRowRead]:
    rows = await pfmea_service.sync_worksheet_from_flowchart(
        db, pfmea_id, current_user.id,
    )
    return [WorksheetRowRead.model_validate(r) for r in rows]


# ============================================================================
# Team Management
# ============================================================================

@router.post(
    "/{pfmea_id}/team",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add team member",
)
async def add_team_member(
    request: Request,
    pfmea_id: int,
    payload: TeamMemberCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(
        RoleChecker(["Administrator", "PFMEA Owner"])
    ),
) -> TeamMemberRead:
    member = await pfmea_service.add_team_member(
        db, pfmea_id, payload, current_user.id,
    )
    
    # Fetch PFMEA details for the email
    pfmea = await pfmea_service.get_pfmea_analysis(db, pfmea_id)
    
    # Commit the transaction explicitly here so the browser's reload doesn't race against the teardown commit
    await db.commit()
    
    if member.user and member.user.email:
        from app.core.config import get_settings
        settings = get_settings()
        base_url = settings.get_allowed_origins[0] if settings.get_allowed_origins else "http://localhost:5173"
        link = f"{base_url}/dashboard/flowchart/{pfmea.flowchart_id}/pfmea" if pfmea.flowchart_id else f"{base_url}/dashboard"
        
        # Get language from request header, default to Spanish
        lang = request.headers.get("Accept-Language", "es")
        if lang.startswith("en"):
            lang = "en"
        else:
            lang = "es"
            
        background_tasks.add_task(
            send_team_assign_notification_email,
            to_email=member.user.email,
            recipient_name=member.user_full_name or "Usuario",
            project_name=pfmea.project_name or "Sin nombre",
            pfmea_id=pfmea.pfmea_id_number or str(pfmea.id),
            part_number=pfmea.part_number or "N/A",
            customer=pfmea.customer or "N/A",
            role_in_team=member.role_in_team,
            department=member.department or "N/A",
            link=link,
            lang=lang
        )

    return TeamMemberRead.model_validate(member)


@router.delete(
    "/{pfmea_id}/team/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove team member",
)
async def remove_team_member(
    pfmea_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(
        RoleChecker(["Administrator", "PFMEA Owner"])
    ),
) -> None:
    await pfmea_service.remove_team_member(
        db, pfmea_id, member_id, current_user.id,
    )


# ============================================================================
# Worksheet Rows (Steps 2–6)
# ============================================================================

@router.get(
    "/{pfmea_id}/worksheet",
    response_model=List[WorksheetRowRead],
    summary="Get all worksheet rows",
    description="Returns all worksheet rows for the specified PFMEA, ordered by sequence.",
)
async def get_worksheet(
    pfmea_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=False)),
) -> List[WorksheetRowRead]:
    rows = await pfmea_service.get_worksheet_rows(db, pfmea_id)
    return [WorksheetRowRead.model_validate(r) for r in rows]


@router.post(
    "/{pfmea_id}/worksheet",
    response_model=WorksheetRowRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add worksheet row",
    description=(
        "Manually add a new row to the worksheet. "
        "AP is auto-calculated if S, O, D are provided."
    ),
)
async def create_worksheet_row(
    pfmea_id: int,
    payload: WorksheetRowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
) -> WorksheetRowRead:
    row = await pfmea_service.create_worksheet_row(
        db, pfmea_id, payload, current_user.id,
    )
    return WorksheetRowRead.model_validate(row)


@router.patch(
    "/{pfmea_id}/worksheet/{row_id}",
    response_model=WorksheetRowRead,
    summary="Update worksheet row",
    description=(
        "Partial update on a single worksheet row. "
        "AP is reactively recalculated if S, O, or D change. "
        "Blocked if PFMEA status is Approved or Archived (HTTP 403)."
    ),
)
async def update_worksheet_row(
    pfmea_id: int,
    row_id: int,
    payload: WorksheetRowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
) -> WorksheetRowRead:
    row = await pfmea_service.update_worksheet_row(
        db, pfmea_id, row_id, payload, current_user.id,
    )
    return WorksheetRowRead.model_validate(row)


@router.put(
    "/{pfmea_id}/worksheet/bulk",
    response_model=List[WorksheetRowRead],
    summary="Bulk update worksheet rows",
    description=(
        "Bulk update or create multiple worksheet rows. "
        "AP is reactively recalculated if S, O, or D change. "
        "Blocked if PFMEA status is Approved or Archived (HTTP 403)."
    ),
)
async def update_worksheet_bulk(
    pfmea_id: int,
    payloads: List[WorksheetRowUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
) -> List[WorksheetRowRead]:
    rows = await pfmea_service.update_worksheet_bulk(
        db, pfmea_id, payloads, current_user.id,
    )
    return [WorksheetRowRead.model_validate(r) for r in rows]


@router.delete(
    "/{pfmea_id}/worksheet/{row_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete worksheet row",
)
async def delete_worksheet_row(
    pfmea_id: int,
    row_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
) -> None:
    await pfmea_service.delete_worksheet_row(
        db, pfmea_id, row_id, current_user.id,
    )


# ============================================================================
# Audit Trail
# ============================================================================

@router.get(
    "/{pfmea_id}/audit-log",
    summary="Get PFMEA audit log",
    description="Returns the immutable audit trail for a specific PFMEA analysis.",
)
async def get_audit_log(
    pfmea_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(PfmeaAccessChecker(require_write=False)),
):
    logs = await pfmea_service.get_pfmea_audit_log(
        db, pfmea_id, skip=skip, limit=limit,
    )
    return [
        {
            "id": log.id,
            "action": log.action,
            "performed_by": log.performed_by,
            "action_details": log.action_details,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "field_name": log.field_name,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "previous_values": log.previous_values,
            "new_values": log.new_values,
            "performed_at": log.performed_at.isoformat() if log.performed_at else None,
        }
        for log in logs
    ]
