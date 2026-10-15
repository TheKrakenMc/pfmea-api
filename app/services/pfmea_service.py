"""PFMEA service — core business logic for the PFMEA worksheet module.

Covers:
- CRUD operations for PFMEA headers (Step 1)
- Flowchart-to-worksheet synchronisation (Steps 2)
- AP lookup algorithm (AIAG-VDA 2019 replacement for RPN)
- MOC status transition gates with high-risk blocking
- Immutability enforcement for Approved/Archived states
- Field-level audit logging
"""

from __future__ import annotations
import logging
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.models.audit_log import AuditLog
from app.models.flowchart import Flowchart
from app.models.flowchart_step import FlowchartStep
from app.models.pfmea_header import PfmeaHeader
from app.models.pfmea_team_member import PfmeaTeamMember
from app.models.pfmea_worksheet_row import PfmeaWorksheetRow
from app.models.plant import Plant
from app.models.product import Product
from app.schemas.pfmea import (
    PfmeaHeaderCreate,
    PfmeaHeaderUpdate,
    TeamMemberCreate,
    WorksheetRowCreate,
    WorksheetRowUpdate,
)


logger = logging.getLogger("pfmea.service")


# ============================================================================
# AIAG-VDA 2019 Action Priority Lookup Table
# ============================================================================
# The official AIAG-VDA FMEA handbook replaces the legacy RPN with an
# Action Priority (AP) matrix. The table below encodes the full 10×10×10
# lookup mapping (S, O, D) → H/M/L.
#
# Key rules (simplified from the official 1,000-cell table):
#   H (High):
#     - Severity ≥ 9 regardless of O and D (safety/regulatory)
#     - Severity ≥ 7 AND Occurrence ≥ 4
#     - Severity ≥ 5 AND Occurrence ≥ 4 AND Detection ≥ 4
#     - Severity ≥ 6 AND Occurrence ≥ 6
#   L (Low):
#     - Severity ≤ 4 AND Occurrence ≤ 3 AND Detection ≤ 3
#     - Severity ≤ 3 AND Occurrence ≤ 3
#     - Severity ≤ 2
#   M (Medium): Everything else


def calculate_action_priority(severity: int, occurrence: int, detection: int) -> str:
    """Calculate Action Priority per AIAG-VDA 2019 methodology.

    Returns:
        "H" (High), "M" (Medium), or "L" (Low)
    """
    if any(
        type(v) is not int or not 1 <= v <= 10
        for v in (severity, occurrence, detection)
    ):
        raise ValueError("S/O/D must be integers from 1 to 10")
    s, o, d = severity, occurrence, detection

    # S = 9-10
    if 9 <= s <= 10:
        if 8 <= o <= 10:
            return "H"
        elif 6 <= o <= 7:
            return "H"
        elif 4 <= o <= 5:
            if d == 1:
                return "M"
            return "H"
        elif 2 <= o <= 3:
            if d >= 7:
                return "H"
            return "M"
        elif o == 1:
            if d >= 7:
                return "H"
            if 5 <= d <= 6:
                return "M"
            return "L"

    # S = 7-8
    elif 7 <= s <= 8:
        if 8 <= o <= 10:
            return "H"
        elif 6 <= o <= 7:
            if d == 1:
                return "M"
            return "H"
        elif 4 <= o <= 5:
            if d >= 5:
                return "H"
            return "M"
        elif 2 <= o <= 3:
            if d >= 5:
                return "M"
            return "L"
        elif o == 1:
            if d >= 7:
                return "M"
            return "L"

    # S = 4-6
    elif 4 <= s <= 6:
        if 8 <= o <= 10:
            if d == 1:
                return "M"
            return "H"
        elif 6 <= o <= 7:
            if d >= 5:
                return "H"
            return "M"
        elif 4 <= o <= 5:
            if d >= 7:
                return "H"
            if 5 <= d <= 6:
                return "M"
            if 2 <= d <= 4:
                return "M"
            return "L"
        elif 2 <= o <= 3:
            if d >= 5:
                return "M"
            return "L"
        elif o == 1:
            if d >= 7:
                return "M"
            return "L"

    # S = 2-3
    elif 2 <= s <= 3:
        if 8 <= o <= 10:
            if d == 1:
                return "L"
            return "M"
        elif 6 <= o <= 7:
            if d >= 5:
                return "M"
            return "L"
        elif 4 <= o <= 5:
            if d >= 7:
                return "M"
            return "L"
        elif 2 <= o <= 3:
            return "L"
        elif o == 1:
            return "L"

    # S = 1
    elif s == 1:
        return "L"

    return "M"


# ============================================================================
# Internal Helpers
# ============================================================================


async def _get_pfmea_or_404(
    db: AsyncSession, pfmea_id: int, *, load_rows: bool = False
) -> PfmeaHeader:
    """Fetch a PFMEA header or raise 404."""
    options = [
        selectinload(PfmeaHeader.team_members).selectinload(PfmeaTeamMember.user),
    ]
    if load_rows:
        options.append(
            selectinload(PfmeaHeader.worksheet_rows).selectinload(
                PfmeaWorksheetRow.responsible_person
            )
        )

    stmt = (
        select(PfmeaHeader)
        .options(*options)
        .where(PfmeaHeader.id == pfmea_id)
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    pfmea = result.scalars().first()
    if pfmea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PFMEA analysis with id {pfmea_id} not found.",
        )
    return pfmea


def _check_immutability(pfmea: PfmeaHeader) -> None:
    """Raise 403 if the PFMEA is in an immutable state."""
    if pfmea.moc_status in ("Approved", "Archived"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"PFMEA is '{pfmea.moc_status}' and cannot be edited.",
        )


async def _generate_hierarchical_id(
    db: AsyncSession, plant_id: Optional[int], version: int = 1
) -> str:
    """Generate the hierarchical ID pattern: [PLANT_CODE]_PFMEA_[SEQ]_[YEAR]_[VERSION]."""
    plant_code = "PLANT"
    if plant_id:
        result = await db.execute(select(Plant.code).where(Plant.id == plant_id))
        code = result.scalar_one_or_none()
        if code:
            plant_code = code.upper().replace(" ", "_")

    year = datetime.now(timezone.utc).year

    from uuid import uuid4

    return f"{plant_code}_PFMEA_{uuid4().hex[:16].upper()}_{year}_{version}"


async def _log_audit(
    db: AsyncSession,
    *,
    pfmea_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    user_id: int,
    field_name: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> None:
    """Insert a field-level audit log entry."""
    log = AuditLog(
        pfmea_project_id=pfmea_id,
        action=action,
        performed_by=user_id,
        action_details=f"{action} on {entity_type}#{entity_id}",
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(log)


# ============================================================================
# CRUD — PFMEA Header (Step 1)
# ============================================================================


async def create_pfmea_analysis(
    db: AsyncSession,
    payload: PfmeaHeaderCreate,
    current_user_id: int,
) -> PfmeaHeader:
    """Create a new PFMEA analysis linked to an existing flowchart."""
    # Validate flowchart exists and join Product for metadata
    fc_result = await db.execute(
        select(Flowchart)
        .options(selectinload(Flowchart.product).selectinload(Product.customer))
        .where(Flowchart.id == payload.flowchart_id)
    )
    flowchart = fc_result.scalars().first()
    if flowchart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flowchart with id {payload.flowchart_id} not found.",
        )

    if flowchart.status != "Approved":
        raise HTTPException(400, "PFMEA requires an approved flowchart")
    plant_id = flowchart.plant_id

    # Sync metadata from Flowchart/Product if not explicitly provided in payload
    # For UI homologation, we want to copy the flowchart's context to PFMEA
    synced_customer = payload.customer
    synced_part_number = payload.part_number
    synced_project_name = payload.project_name

    if flowchart.product:
        if not synced_customer and flowchart.product.customer_name:
            synced_customer = flowchart.product.customer_name
        if not synced_part_number and flowchart.product.part_number:
            synced_part_number = flowchart.product.part_number
        if not synced_project_name and flowchart.product.description:
            synced_project_name = flowchart.product.description

    # Generate hierarchical ID
    hierarchical_id = await _generate_hierarchical_id(db, plant_id)

    pfmea = PfmeaHeader(
        flowchart_id=payload.flowchart_id,
        pfmea_id_number=hierarchical_id,
        project_name=synced_project_name,
        customer=synced_customer,
        original_launch_date=payload.original_launch_date,
        part_number=synced_part_number,
        product_description=payload.product_description,
        product_family_id=payload.product_family_id,
        production_line_id=payload.production_line_id,
        confidentiality_level=payload.confidentiality_level,
        moc_status="Draft",
        status="Draft",
        plant_id=plant_id,
        owner_id=current_user_id,
        start_date=date.today(),
    )
    db.add(pfmea)
    await db.flush()

    # Add team members (always include the creator as PFMEA Owner)
    creator_in_team = False
    from app.models import User
    from app.models.auth_session import UserPlant

    for tm in payload.team_members:
        candidate = await db.get(User, tm.user_id)
        assignment = await db.get(UserPlant, (tm.user_id, plant_id))
        if (
            not candidate
            or not candidate.is_active
            or candidate.deleted_at is not None
            or (tm.user_id != current_user_id and assignment is None)
        ):
            raise HTTPException(
                400, "Team members must be active and assigned to this plant"
            )
        if tm.user_id == current_user_id:
            creator_in_team = True
        db.add(
            PfmeaTeamMember(
                pfmea_id=pfmea.id,
                user_id=tm.user_id,
                role_in_team="PFMEA Owner"
                if tm.user_id == current_user_id
                else tm.role_in_team,
            )
        )

    if not creator_in_team:
        db.add(
            PfmeaTeamMember(
                pfmea_id=pfmea.id,
                user_id=current_user_id,
                role_in_team="PFMEA Owner",
            )
        )

    await db.flush()

    # Audit
    await _log_audit(
        db,
        pfmea_id=pfmea.id,
        entity_type="pfmea_header",
        entity_id=pfmea.id,
        action="CREATE",
        user_id=current_user_id,
        new_value=hierarchical_id,
    )

    return await _get_pfmea_or_404(db, pfmea.id)


async def get_pfmea_analysis(db: AsyncSession, pfmea_id: int) -> PfmeaHeader:
    """Get a single PFMEA analysis with full detail (team + rows)."""
    return await _get_pfmea_or_404(db, pfmea_id, load_rows=True)


async def list_pfmea_analyses(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    plant_id: Optional[int] = None,
    owner_id: Optional[int] = None,
) -> list[PfmeaHeader]:
    """Return a paginated list of PFMEA analyses (without rows for performance)."""
    stmt = (
        select(PfmeaHeader)
        .options(
            selectinload(PfmeaHeader.team_members).selectinload(PfmeaTeamMember.user)
        )
        .order_by(PfmeaHeader.id.desc())
        .offset(skip)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(PfmeaHeader.moc_status == status_filter)
    if plant_id:
        stmt = stmt.where(PfmeaHeader.plant_id == plant_id)
    if owner_id:
        stmt = stmt.where(PfmeaHeader.owner_id == owner_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_pfmea_header(
    db: AsyncSession,
    pfmea_id: int,
    payload: PfmeaHeaderUpdate,
    current_user_id: int,
) -> PfmeaHeader:
    """Update Step 1 metadata (project info). Blocks if Approved/Archived."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    update_data = payload.model_dump(exclude_unset=True)
    for controlled in ("plant_id", "version"):
        if controlled in update_data and update_data[controlled] != getattr(
            pfmea, controlled
        ):
            raise HTTPException(
                400, "Plant and revision are controlled by document lifecycle"
            )
        update_data.pop(controlled, None)
    for field, new_val in update_data.items():
        old_val = getattr(pfmea, field, None)
        if old_val != new_val:
            setattr(pfmea, field, new_val)
            await _log_audit(
                db,
                pfmea_id=pfmea_id,
                entity_type="pfmea_header",
                entity_id=pfmea_id,
                action="UPDATE",
                user_id=current_user_id,
                field_name=field,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
            )

    db.add(pfmea)
    await db.flush()
    return await _get_pfmea_or_404(db, pfmea_id)


# ============================================================================
# Team Management
# ============================================================================


async def add_team_member(
    db: AsyncSession,
    pfmea_id: int,
    payload: TeamMemberCreate,
    current_user_id: int,
) -> PfmeaTeamMember:
    """Add a member to the PFMEA core team."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    from app.models.user import User
    from app.models.auth_session import UserPlant

    candidate = await db.get(User, payload.user_id)
    assignment = (
        await db.get(UserPlant, (payload.user_id, pfmea.plant_id))
        if pfmea.plant_id
        else None
    )
    if not candidate or not candidate.is_active or assignment is None:
        raise HTTPException(
            400, "Team members must be active and assigned to this plant"
        )
    member = PfmeaTeamMember(
        pfmea_id=pfmea_id,
        user_id=payload.user_id,
        role_in_team=payload.role_in_team,
        department=payload.department,
    )
    db.add(member)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a team member for this PFMEA.",
        )

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_team_member",
        entity_id=member.id,
        action="CREATE",
        user_id=current_user_id,
        new_value=f"user_id={payload.user_id}, role={payload.role_in_team}",
    )
    stmt = (
        select(PfmeaTeamMember)
        .options(selectinload(PfmeaTeamMember.user))
        .where(PfmeaTeamMember.id == member.id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def remove_team_member(
    db: AsyncSession,
    pfmea_id: int,
    member_id: int,
    current_user_id: int,
) -> None:
    """Remove a member from the PFMEA core team."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    result = await db.execute(
        select(PfmeaTeamMember).where(
            PfmeaTeamMember.id == member_id,
            PfmeaTeamMember.pfmea_id == pfmea_id,
        )
    )
    member = result.scalars().first()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team member {member_id} not found in PFMEA {pfmea_id}.",
        )

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_team_member",
        entity_id=member_id,
        action="DELETE",
        user_id=current_user_id,
        old_value=f"user_id={member.user_id}, role={member.role_in_team}",
    )
    await db.delete(member)
    await db.flush()


# ============================================================================
# Flowchart → Worksheet Synchronisation
# ============================================================================


async def sync_worksheet_from_flowchart(
    db: AsyncSession,
    pfmea_id: int,
    current_user_id: int,
) -> list[PfmeaWorksheetRow]:
    """Populate/update worksheet rows from the linked flowchart steps.

    Creates one row per flowchart step that doesn't already have a mapped row.
    Existing rows are updated with fresh structure-analysis data.
    """
    pfmea = await _get_pfmea_or_404(db, pfmea_id, load_rows=True)
    _check_immutability(pfmea)

    if pfmea.flowchart_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PFMEA has no linked flowchart to synchronise from.",
        )

    # Load flowchart steps with technology and machinery
    fc_result = await db.execute(
        select(FlowchartStep)
        .options(
            joinedload(FlowchartStep.technology),
            joinedload(FlowchartStep.machinery),
        )
        .where(FlowchartStep.flowchart_id == pfmea.flowchart_id)
        .order_by(FlowchartStep.step_number, FlowchartStep.sub_step)
    )
    steps = list(fc_result.unique().scalars().all())

    if not steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Linked flowchart has no steps to synchronise.",
        )

    # Map existing rows by flowchart_step_id
    existing_map: dict[int, list[PfmeaWorksheetRow]] = {}
    for row in pfmea.worksheet_rows:
        if row.flowchart_step_id:
            existing_map.setdefault(row.flowchart_step_id, []).append(row)

    created_rows: list[PfmeaWorksheetRow] = []
    for idx, step in enumerate(steps):
        # Build structure-analysis fields from step
        tech_name = step.technology.name if step.technology else None
        step_label = (
            f"{step.step_number}.{step.sub_step}"
            if step.sub_step > 0
            else f"{step.step_number}"
        )

        station_name = f"Step {step_label}"
        if step.responsible_department:
            station_name = f"{step.responsible_department} - Step {step_label}"

        desc_label = step.custom_description or tech_name
        operation_desc = (
            f"{station_name} - {desc_label}" if desc_label else station_name
        )

        # Merge product_characteristics and target for default PROCESS FUNCTION REQUIREMENTS
        merged_req_parts = []
        if step.product_characteristics and step.product_characteristics.strip():
            merged_req_parts.append(f"- {step.product_characteristics.strip()}")
        if step.target and step.target.strip():
            merged_req_parts.append(step.target.strip())
        default_func_req = "\n".join(merged_req_parts) if merged_req_parts else None

        if step.id in existing_map:
            # Update existing rows with fresh structure data without overwriting custom user inputs
            for existing_row in existing_map[step.id]:
                existing_row.process_item_name = (
                    pfmea.part_number or existing_row.process_item_name
                )
                existing_row.station_operation = operation_desc
                existing_row.operation_type = step.symbol_type
                if (
                    not existing_row.function_process_step
                    or not existing_row.function_process_step.strip()
                ):
                    if default_func_req:
                        existing_row.function_process_step = default_func_req
                if (
                    not existing_row.product_characteristic
                    or not existing_row.product_characteristic.strip()
                ):
                    existing_row.product_characteristic = step.product_characteristics
                if (
                    not existing_row.process_characteristic
                    or not existing_row.process_characteristic.strip()
                ):
                    existing_row.process_characteristic = step.process_characteristics
                db.add(existing_row)
        else:
            # Create new row
            new_row = PfmeaWorksheetRow(
                pfmea_id=pfmea_id,
                flowchart_step_id=step.id,
                process_item_name=pfmea.part_number,
                station_operation=operation_desc,
                operation_type=step.symbol_type,
                function_process_step=default_func_req,
                product_characteristic=step.product_characteristics,
                process_characteristic=step.process_characteristics,
                sequence_order=(idx + 1) * 10,
            )
            db.add(new_row)
            created_rows.append(new_row)

    await db.flush()

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_worksheet",
        entity_id=pfmea_id,
        action="SYNC_FLOWCHART",
        user_id=current_user_id,
        new_value=f"Synced {len(created_rows)} new rows from {len(steps)} flowchart steps",
    )

    # Re-fetch to return full data
    pfmea = await _get_pfmea_or_404(db, pfmea_id, load_rows=True)
    return list(pfmea.worksheet_rows)


# ============================================================================
# Worksheet Row CRUD (Steps 2–6)
# ============================================================================


async def get_worksheet_rows(
    db: AsyncSession, pfmea_id: int
) -> list[PfmeaWorksheetRow]:
    """Get all worksheet rows for a PFMEA, ordered by sequence."""
    await _get_pfmea_or_404(db, pfmea_id)  # Validate existence
    result = await db.execute(
        select(PfmeaWorksheetRow)
        .options(selectinload(PfmeaWorksheetRow.responsible_person))
        .where(PfmeaWorksheetRow.pfmea_id == pfmea_id)
        .order_by(PfmeaWorksheetRow.sequence_order)
    )
    return list(result.scalars().all())


async def create_worksheet_row(
    db: AsyncSession,
    pfmea_id: int,
    payload: WorksheetRowCreate,
    current_user_id: int,
) -> PfmeaWorksheetRow:
    """Manually add a worksheet row to an existing PFMEA."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    data = payload.model_dump(exclude_unset=True)
    await _validate_row_references(db, pfmea, data)
    if data.get("action_status") == "Completed":
        raise HTTPException(400, "Use action confirmation")
    data["pfmea_id"] = pfmea_id

    # Auto-calculate AP if S, O, D are all provided
    s, o, d = data.get("severity"), data.get("occurrence"), data.get("detection")
    if s is not None and o is not None and d is not None:
        data["action_priority"] = calculate_action_priority(s, o, d)

    # Auto-calculate new AP if new S, O, D are provided
    ns, no, nd = (
        data.get("new_severity"),
        data.get("new_occurrence"),
        data.get("new_detection"),
    )
    if ns is not None and no is not None and nd is not None:
        data["new_action_priority"] = calculate_action_priority(ns, no, nd)

    row = PfmeaWorksheetRow(**data)
    db.add(row)
    await db.flush()
    await db.refresh(row)

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_worksheet_row",
        entity_id=row.id,
        action="CREATE",
        user_id=current_user_id,
    )

    return row


async def update_worksheet_row(
    db: AsyncSession,
    pfmea_id: int,
    row_id: int,
    payload: WorksheetRowUpdate,
    current_user_id: int,
) -> PfmeaWorksheetRow:
    """Update a single worksheet row (PATCH). Re-calculates AP reactively."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    result = await db.execute(
        select(PfmeaWorksheetRow).where(
            PfmeaWorksheetRow.id == row_id,
            PfmeaWorksheetRow.pfmea_id == pfmea_id,
        )
    )
    row = result.scalars().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worksheet row {row_id} not found in PFMEA {pfmea_id}.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    await _validate_row_references(db, pfmea, update_data)
    if update_data.get("action_status") == "Completed":
        raise HTTPException(400, "Use action confirmation")
    for field, new_val in update_data.items():
        old_val = getattr(row, field, None)
        if old_val != new_val:
            setattr(row, field, new_val)
            await _log_audit(
                db,
                pfmea_id=pfmea_id,
                entity_type="pfmea_worksheet_row",
                entity_id=row_id,
                action="UPDATE",
                user_id=current_user_id,
                field_name=field,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
            )

    # Reactively recalculate AP if S, O, or D changed
    s = row.severity
    o = row.occurrence
    d = row.detection
    if s is not None and o is not None and d is not None:
        new_ap = calculate_action_priority(s, o, d)
        if row.action_priority != new_ap:
            await _log_audit(
                db,
                pfmea_id=pfmea_id,
                entity_type="pfmea_worksheet_row",
                entity_id=row_id,
                action="UPDATE",
                user_id=current_user_id,
                field_name="action_priority",
                old_value=row.action_priority,
                new_value=new_ap,
            )
            row.action_priority = new_ap

    # Recalculate new AP if new ratings changed
    ns = row.new_severity
    no = row.new_occurrence
    nd = row.new_detection
    if ns is not None and no is not None and nd is not None:
        new_new_ap = calculate_action_priority(ns, no, nd)
        if row.new_action_priority != new_new_ap:
            row.new_action_priority = new_new_ap

    _invalidate_action_validation(row)

    db.add(row)
    await db.flush()
    await db.refresh(row)

    # Check if Control Plan exists and if we should sync
    from app.services.control_plan_service import (
        get_control_plan_by_pfmea,
        sync_critical_items,
    )

    cp = await get_control_plan_by_pfmea(db, pfmea_id)
    if cp:
        if cp.status in {"Approved", "Archived"}:
            cp.needs_review = True
        else:
            await sync_critical_items(db, cp.id, current_user_id)

    return row


async def update_worksheet_bulk(
    db: AsyncSession,
    pfmea_id: int,
    payloads: list[WorksheetRowUpdate],
    current_user_id: int,
    deleted_row_ids: list[int] | None = None,
) -> list[PfmeaWorksheetRow]:
    """Bulk update or create multiple worksheet rows."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    # Pre-fetch existing rows to avoid N+1
    result = await db.execute(
        select(PfmeaWorksheetRow).where(PfmeaWorksheetRow.pfmea_id == pfmea_id)
    )
    existing_rows_map = {row.id: row for row in result.scalars().all()}

    # Identify rows to delete (exist in DB but not in payload)
    delete_ids = set(deleted_row_ids or [])
    if not delete_ids.issubset(existing_rows_map):
        raise HTTPException(400, "Deleted rows must belong to this document")
    for row_id, row in existing_rows_map.items():
        if row_id in delete_ids:
            await db.delete(row)
            await _log_audit(
                db,
                pfmea_id=pfmea_id,
                entity_type="pfmea_worksheet_row",
                entity_id=row_id,
                action="DELETE",
                user_id=current_user_id,
            )

    updated_rows = []

    for payload in payloads:
        data = payload.model_dump(exclude_unset=True)
        await _validate_row_references(db, pfmea, data)
        if data.get("action_status") == "Completed":
            data.pop("action_status")
        # Drop the id from data if present to avoid updating primary key
        row_id = data.pop("id", None)

        # Determine AP
        s, o, d = data.get("severity"), data.get("occurrence"), data.get("detection")
        ns, no, nd = (
            data.get("new_severity"),
            data.get("new_occurrence"),
            data.get("new_detection"),
        )

        if row_id and row_id > 0 and row_id not in existing_rows_map:
            raise HTTPException(400, "Row does not belong to this document")
        if row_id in delete_ids:
            raise HTTPException(400, "Cannot update and delete the same row")
        if row_id and row_id in existing_rows_map:
            row = existing_rows_map[row_id]
            evidence_changed = any(
                getattr(row, k, None) != v
                for k, v in data.items()
                if k not in {"sequence_order", "action_status"}
            )
            for field, new_val in data.items():
                old_val = getattr(row, field, None)
                if old_val != new_val:
                    setattr(row, field, new_val)
                    await _log_audit(
                        db,
                        pfmea_id=pfmea_id,
                        entity_type="pfmea_worksheet_row",
                        entity_id=row_id,
                        action="UPDATE",
                        user_id=current_user_id,
                        field_name=field,
                        old_value=str(old_val) if old_val is not None else None,
                        new_value=str(new_val) if new_val is not None else None,
                    )
            # Re-eval AP based on current row state
            rs, ro, rd = row.severity, row.occurrence, row.detection
            if rs is not None and ro is not None and rd is not None:
                new_ap = calculate_action_priority(rs, ro, rd)
                if row.action_priority != new_ap:
                    row.action_priority = new_ap

            rns, rno, rnd = row.new_severity, row.new_occurrence, row.new_detection
            if rns is not None and rno is not None and rnd is not None:
                new_new_ap = calculate_action_priority(rns, rno, rnd)
                if row.new_action_priority != new_new_ap:
                    row.new_action_priority = new_new_ap

            if evidence_changed:
                _invalidate_action_validation(row)

            db.add(row)
            updated_rows.append(row)
        else:
            # Create new row
            data["pfmea_id"] = pfmea_id
            if s is not None and o is not None and d is not None:
                data["action_priority"] = calculate_action_priority(s, o, d)
            if ns is not None and no is not None and nd is not None:
                data["new_action_priority"] = calculate_action_priority(ns, no, nd)
            if data.get("action_status") == "Completed":
                raise HTTPException(400, "Use action confirmation")

            new_row = PfmeaWorksheetRow(**data)
            db.add(new_row)
            await db.flush()  # Need ID for log
            await db.refresh(
                new_row
            )  # Need created_at/updated_at for Pydantic response
            await _log_audit(
                db,
                pfmea_id=pfmea_id,
                entity_type="pfmea_worksheet_row",
                entity_id=new_row.id,
                action="CREATE",
                user_id=current_user_id,
            )
            updated_rows.append(new_row)

    await db.flush()

    for r in updated_rows:
        await db.refresh(r)

    if updated_rows or delete_ids:
        from app.services.control_plan_service import (
            get_control_plan_by_pfmea,
            sync_critical_items,
        )

        cp = await get_control_plan_by_pfmea(db, pfmea_id)
        if cp:
            if cp.status in {"Approved", "Archived"}:
                cp.needs_review = True
            else:
                await sync_critical_items(db, cp.id, current_user_id)

    return updated_rows


async def delete_worksheet_row(
    db: AsyncSession,
    pfmea_id: int,
    row_id: int,
    current_user_id: int,
) -> None:
    """Delete a worksheet row."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)

    result = await db.execute(
        select(PfmeaWorksheetRow).where(
            PfmeaWorksheetRow.id == row_id,
            PfmeaWorksheetRow.pfmea_id == pfmea_id,
        )
    )
    row = result.scalars().first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worksheet row {row_id} not found in PFMEA {pfmea_id}.",
        )

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_worksheet_row",
        entity_id=row_id,
        action="DELETE",
        user_id=current_user_id,
    )
    await db.delete(row)
    await db.flush()


# ============================================================================
# MOC Status Transitions (State Machine)
# ============================================================================

# Valid transitions map
_VALID_TRANSITIONS: dict[str, list[str]] = {
    "Draft": ["In Review"],
    "In Review": ["Draft", "Approved"],
    "Approved": ["Archived"],
    "Archived": [],  # Terminal state (Admin can restore to Draft via separate endpoint)
}


async def transition_moc_status(
    db: AsyncSession,
    pfmea_id: int,
    new_status: str,
    current_user_id: int,
) -> PfmeaHeader:
    """Transition the MOC status of a PFMEA analysis.

    Gate rules:
    - Draft → In Review: Steps 1-5 must have at least one row
    - In Review → Approved: BLOCKS if any row has AP='H'
      with action_status != 'Completed' (Step 6 unresolved)
    - Approved → Archived: Only Admin/Owner
    """
    pfmea = await _get_pfmea_or_404(db, pfmea_id, load_rows=True)
    old_status = pfmea.moc_status

    # Validate transition is allowed
    allowed = _VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition from '{old_status}' to '{new_status}'. "
                f"Allowed transitions: {allowed}"
            ),
        )

    # ── Gate: Draft → In Review ───────────────────────────────
    if old_status == "Draft" and new_status == "In Review":
        if not pfmea.worksheet_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit for review: worksheet has no rows. "
                "Complete Steps 2-5 first.",
            )
        # Check that at least basic fields are filled
        incomplete_rows = [
            r
            for r in pfmea.worksheet_rows
            if not r.failure_mode
            or r.severity is None
            or r.occurrence is None
            or r.detection is None
        ]
        if incomplete_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot submit: {len(incomplete_rows)} rows have incomplete "
                    f"failure analysis (Steps 3-5). All rows must have failure_mode, "
                    f"severity, occurrence, and detection filled."
                ),
            )

    # ── Gate: In Review → Approved ────────────────────────────
    if old_status == "In Review" and new_status == "Approved":
        high_risk_unresolved = [
            r
            for r in pfmea.worksheet_rows
            if (r.action_priority == "H" or (r.severity or 0) >= 9)
            and not _action_is_validated(r)
        ]
        if high_risk_unresolved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Aprobación bloqueada: {len(high_risk_unresolved)} fila(s) con Prioridad de Acción Alta (H) "
                    f"no han sido resueltas en Optimización (Paso 6). Documente las acciones tomadas y nuevas calificaciones (S, O, D) "
                    f"y solicite la validación explícita del Owner antes de aprobar."
                ),
            )

    if new_status == "Approved":
        pfmea.needs_review = False
        pfmea.revision_date = date.today()
    # Apply transition
    pfmea.moc_status = new_status
    pfmea.status = new_status  # Keep both fields in sync
    if new_status == "Approved":
        await db.flush()
        await _snapshot_pfmea(db, pfmea, current_user_id, "Approved")

    db.add(pfmea)
    await db.flush()

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_header",
        entity_id=pfmea_id,
        action="STATUS_TRANSITION",
        user_id=current_user_id,
        field_name="moc_status",
        old_value=old_status,
        new_value=new_status,
    )

    return await _get_pfmea_or_404(db, pfmea_id)


# ============================================================================
# Admin: Restore to Draft
# ============================================================================


async def restore_to_draft(
    db: AsyncSession, pfmea_id: int, current_user_id: int
) -> PfmeaHeader:
    """Admin-only: restore an Archived PFMEA back to Draft, incrementing version."""
    pfmea = await _get_pfmea_or_404(db, pfmea_id)

    if pfmea.moc_status not in ("Approved", "Archived"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only restore Approved or Archived analyses.",
        )

    await _snapshot_pfmea(db, pfmea, current_user_id, "Before reopening")
    from app.models import ControlPlan
    plan=(await db.scalars(select(ControlPlan).where(ControlPlan.pfmea_project_id==pfmea_id))).first()
    if plan:
        plan.needs_review=True
    old_status = pfmea.moc_status
    pfmea.moc_status = "Draft"
    pfmea.status = "Draft"
    pfmea.version = pfmea.version + 1

    # Regenerate the hierarchical ID with the new version
    parts = pfmea.pfmea_id_number.rsplit("_", 1) if pfmea.pfmea_id_number else []
    if len(parts) == 2:
        pfmea.pfmea_id_number = f"{parts[0]}_{pfmea.version}"

    db.add(pfmea)
    await db.flush()

    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_header",
        entity_id=pfmea_id,
        action="RESTORE_TO_DRAFT",
        user_id=current_user_id,
        field_name="moc_status",
        old_value=old_status,
        new_value="Draft",
    )

    return await _get_pfmea_or_404(db, pfmea_id)


# ============================================================================
# Audit Trail Query
# ============================================================================


async def get_pfmea_audit_log(
    db: AsyncSession,
    pfmea_id: int,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[AuditLog]:
    """Get all audit log entries for a specific PFMEA analysis."""
    await _get_pfmea_or_404(db, pfmea_id)
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.pfmea_project_id == pfmea_id)
        .order_by(AuditLog.performed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ============================================================================
# My Tasks (Pending Actions for current user)
# ============================================================================


async def get_my_tasks(
    db: AsyncSession,
    current_user_id: int,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Get all pending action items assigned to the current user.

    Returns worksheet rows where:
    - responsible_person_id = current_user_id
    - action_status != 'Completed'
    - PFMEA is not Archived
    """
    stmt = (
        select(
            PfmeaWorksheetRow.id.label("row_id"),
            PfmeaWorksheetRow.pfmea_id,
            PfmeaHeader.pfmea_id_number,
            PfmeaHeader.project_name,
            PfmeaWorksheetRow.failure_mode,
            PfmeaWorksheetRow.action_priority,
            PfmeaWorksheetRow.optimization_prevention_action,
            PfmeaWorksheetRow.optimization_detection_action,
            PfmeaWorksheetRow.target_completion_date,
            PfmeaWorksheetRow.action_status,
        )
        .join(PfmeaHeader, PfmeaWorksheetRow.pfmea_id == PfmeaHeader.id)
        .where(
            PfmeaWorksheetRow.responsible_person_id == current_user_id,
            PfmeaWorksheetRow.action_status != "Completed",
            PfmeaHeader.moc_status.notin_(["Archived"]),
        )
        .order_by(
            # H first, then M, then L
            case(
                (PfmeaWorksheetRow.action_priority == "H", 1),
                (PfmeaWorksheetRow.action_priority == "M", 2),
                else_=3,
            ),
            PfmeaWorksheetRow.target_completion_date.asc().nulls_last(),
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [dict(row._mapping) for row in rows]


# ============================================================================
# AP Lookup Utility
# ============================================================================


def ap_lookup(severity: int, occurrence: int, detection: int) -> str:
    """Public utility: calculate AP for given S/O/D values."""
    return calculate_action_priority(severity, occurrence, detection)


def _invalidate_action_validation(row):
    if row.validated_by is not None:
        row.validated_by = None
        row.validated_at = None
    if row.action_status == "Completed":
        row.action_status = "In Progress"
    if any(v is None for v in (row.severity, row.occurrence, row.detection)):
        row.action_priority = None
    if any(
        v is None for v in (row.new_severity, row.new_occurrence, row.new_detection)
    ):
        row.new_action_priority = None


def _action_is_validated(row):
    return bool(
        row.action_status == "Completed"
        and row.validated_by
        and row.validated_at
        and row.actions_taken
        and row.actions_taken.strip()
        and row.responsible_person_id
        and row.completion_date
        and all(
            v is not None
            for v in (row.new_severity, row.new_occurrence, row.new_detection)
        )
    )


async def confirm_action(db, pfmea_id, row_id, actor_id):
    pfmea = await _get_pfmea_or_404(db, pfmea_id)
    _check_immutability(pfmea)
    row = (
        await db.scalars(
            select(PfmeaWorksheetRow).where(
                PfmeaWorksheetRow.id == row_id, PfmeaWorksheetRow.pfmea_id == pfmea_id
            )
        )
    ).first()
    if not row:
        raise HTTPException(404, "Row not found")
    if not (
        row.actions_taken
        and row.actions_taken.strip()
        and row.responsible_person_id
        and row.completion_date
        and all(
            v is not None
            for v in (row.new_severity, row.new_occurrence, row.new_detection)
        )
    ):
        raise HTTPException(
            400,
            "Action evidence, responsible person, completion date and new S/O/D are required",
        )
    from app.models.user import User

    person = await db.get(User, row.responsible_person_id)
    membership = (
        await db.scalars(
            select(PfmeaTeamMember).where(
                PfmeaTeamMember.pfmea_id == pfmea_id,
                PfmeaTeamMember.user_id == row.responsible_person_id,
            )
        )
    ).first()
    if (
        not person
        or not person.is_active
        or (not membership and pfmea.owner_id != person.id)
    ):
        raise HTTPException(400, "Responsible person must be an active project member")
    if row.completion_date > date.today():
        raise HTTPException(400, "Completion date cannot be in the future")
    row.responsible_person = person
    row.action_status = "Completed"
    row.validated_by = actor_id
    row.validated_at = datetime.now(timezone.utc)
    await _log_audit(
        db,
        pfmea_id=pfmea_id,
        entity_type="pfmea_worksheet_row",
        entity_id=row.id,
        action="ACTION_CONFIRMED",
        user_id=actor_id,
    )
    await db.flush()
    return row


async def _snapshot_pfmea(db, pfmea, actor_id, reason):
    from app.models.document_version import DocumentVersion
    from app.schemas.pfmea import PfmeaHeaderDetailRead

    detail = await _get_pfmea_or_404(db, pfmea.id, load_rows=True)
    db.add(
        DocumentVersion(
            document_type="pfmea",
            document_id=pfmea.id,
            revision_number=pfmea.version,
            change_reason=reason,
            created_by=actor_id,
            original_creation_date=pfmea.created_at,
            snapshot_data=PfmeaHeaderDetailRead.model_validate(detail).model_dump(
                mode="json"
            ),
            is_initial_revision=False,
        )
    )
    await db.flush()


async def _validate_row_references(db, pfmea, data):
    if data.get("flowchart_step_id"):
        step = await db.get(FlowchartStep, data["flowchart_step_id"])
        if not step or step.flowchart_id != pfmea.flowchart_id:
            raise HTTPException(400, "Operation must belong to the linked diagram")
    if data.get("responsible_person_id"):
        from app.models.user import User

        person = await db.get(User, data["responsible_person_id"])
        member = (
            await db.scalars(
                select(PfmeaTeamMember).where(
                    PfmeaTeamMember.pfmea_id == pfmea.id,
                    PfmeaTeamMember.user_id == data["responsible_person_id"],
                )
            )
        ).first()
        if (
            not person
            or not person.is_active
            or (not member and pfmea.owner_id != person.id)
        ):
            raise HTTPException(
                400, "Responsible person must be an active member of the project"
            )
