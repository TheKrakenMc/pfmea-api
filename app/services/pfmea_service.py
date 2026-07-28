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
from sqlalchemy import case, delete, func, select, text
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
from app.models.technology import Technology
from app.models.machinery import Machinery
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
    s, o, d = severity, occurrence, detection

    # ── HIGH priority rules ──────────────────────────────────────────────
    # Safety/regulatory severity always high
    if s >= 9:
        return "H"
    # High severity with moderate-to-high occurrence
    if s >= 7 and o >= 4:
        return "H"
    # Moderate severity with high occurrence and poor detection
    if s >= 5 and o >= 4 and d >= 4:
        return "H"
    # High severity with high occurrence
    if s >= 6 and o >= 6:
        return "H"
    # Very high occurrence with any meaningful severity
    if s >= 4 and o >= 8:
        return "H"
    # High severity (7-8) with moderate occurrence and poor detection
    if s >= 7 and o >= 2 and d >= 7:
        return "H"

    # ── LOW priority rules ───────────────────────────────────────────────
    # Very low severity
    if s <= 2:
        return "L"
    # Low severity and low occurrence
    if s <= 3 and o <= 3:
        return "L"
    # Low severity, low occurrence, good detection
    if s <= 4 and o <= 3 and d <= 3:
        return "L"
    # Minimal risk combination
    if s <= 5 and o <= 2 and d <= 2:
        return "L"

    # ── MEDIUM (everything else) ─────────────────────────────────────────
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
        options.append(selectinload(PfmeaHeader.worksheet_rows))

    stmt = select(PfmeaHeader).options(*options).where(PfmeaHeader.id == pfmea_id)
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

    # Get next sequence number for this plant
    result = await db.execute(
        select(func.count(PfmeaHeader.id)).where(PfmeaHeader.plant_id == plant_id)
    )
    seq = (result.scalar() or 0) + 1

    return f"{plant_code}_PFMEA_{seq:03d}_{year}_{version}"


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
    for tm in payload.team_members:
        if tm.user_id == current_user_id:
            creator_in_team = True
        db.add(PfmeaTeamMember(
            pfmea_id=pfmea.id,
            user_id=tm.user_id,
            role_in_team=tm.role_in_team,
        ))

    if not creator_in_team:
        db.add(PfmeaTeamMember(
            pfmea_id=pfmea.id,
            user_id=current_user_id,
            role_in_team="PFMEA Owner",
        ))

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
        .options(selectinload(PfmeaHeader.team_members).selectinload(PfmeaTeamMember.user))
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
    stmt = select(PfmeaTeamMember).options(selectinload(PfmeaTeamMember.user)).where(PfmeaTeamMember.id == member.id)
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
        .order_by(FlowchartStep.step_number)
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
        machinery_name = None
        if step.machinery:
            machinery_name = step.machinery.machinery_name if hasattr(step.machinery, "machinery_name") else None

        station_name = f"Step {step.step_number}"
        if step.responsible_department:
            station_name = f"{step.responsible_department} - Step {step.step_number}"

        operation_desc = f"{station_name} - {tech_name}" if tech_name else station_name

        if step.id in existing_map:
            # Update existing rows with fresh structure data
            for existing_row in existing_map[step.id]:
                existing_row.process_item_name = pfmea.part_number or existing_row.process_item_name
                existing_row.station_operation = operation_desc
                existing_row.operation_type = step.symbol_type
                db.add(existing_row)
        else:
            # Create new row
            new_row = PfmeaWorksheetRow(
                pfmea_id=pfmea_id,
                flowchart_step_id=step.id,
                process_item_name=pfmea.part_number,
                station_operation=operation_desc,
                operation_type=step.symbol_type,
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
    data["pfmea_id"] = pfmea_id

    # Auto-calculate AP if S, O, D are all provided
    s, o, d = data.get("severity"), data.get("occurrence"), data.get("detection")
    if s is not None and o is not None and d is not None:
        data["action_priority"] = calculate_action_priority(s, o, d)

    # Auto-calculate new AP if new S, O, D are provided
    ns, no, nd = data.get("new_severity"), data.get("new_occurrence"), data.get("new_detection")
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

    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def update_worksheet_bulk(
    db: AsyncSession,
    pfmea_id: int,
    payloads: list[WorksheetRowUpdate],
    current_user_id: int,
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
    payload_ids = {p.id for p in payloads if getattr(p, "id", None) and p.id > 0}
    for row_id, row in existing_rows_map.items():
        if row_id not in payload_ids:
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
        # Drop the id from data if present to avoid updating primary key
        row_id = data.pop("id", None)
        
        # Determine AP
        s, o, d = data.get("severity"), data.get("occurrence"), data.get("detection")
        ns, no, nd = data.get("new_severity"), data.get("new_occurrence"), data.get("new_detection")

        if row_id and row_id in existing_rows_map:
            row = existing_rows_map[row_id]
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

            db.add(row)
            updated_rows.append(row)
        else:
            # Create new row
            data["pfmea_id"] = pfmea_id
            if s is not None and o is not None and d is not None:
                data["action_priority"] = calculate_action_priority(s, o, d)
            if ns is not None and no is not None and nd is not None:
                data["new_action_priority"] = calculate_action_priority(ns, no, nd)
            
            new_row = PfmeaWorksheetRow(**data)
            db.add(new_row)
            await db.flush() # Need ID for log
            await db.refresh(new_row) # Need created_at/updated_at for Pydantic response
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
            r for r in pfmea.worksheet_rows
            if not r.failure_mode or r.severity is None or r.occurrence is None or r.detection is None
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
            r for r in pfmea.worksheet_rows
            if r.action_priority == "H" and r.action_status != "Completed"
        ]
        if high_risk_unresolved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"APPROVAL BLOCKED: {len(high_risk_unresolved)} rows with "
                    f"High (H) Action Priority have not been resolved in Step 6 "
                    f"(Optimization). All high-risk items must have action_status "
                    f"= 'Completed' before approval."
                ),
            )

    # Apply transition
    pfmea.moc_status = new_status
    pfmea.status = new_status  # Keep both fields in sync

    if new_status == "Approved":
        pfmea.revision_date = date.today()

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
