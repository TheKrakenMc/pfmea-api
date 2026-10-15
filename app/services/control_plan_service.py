"""Control plans preserve source identity and operational controls."""

from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models import (
    ControlPlan,
    ControlPlanItem,
    PfmeaHeader,
    PfmeaWorksheetRow,
    AuditLog,
    DocumentVersion,
)


async def _get_control_plan_or_404(db, control_plan_id):
    cp = (
        await db.scalars(
            select(ControlPlan)
            .options(selectinload(ControlPlan.items))
            .where(ControlPlan.id == control_plan_id)
        )
    ).first()
    if cp is None:
        raise HTTPException(404, "Control Plan not found")
    return cp


async def get_control_plan_by_pfmea(db, pfmea_id):
    return (
        await db.scalars(
            select(ControlPlan)
            .options(selectinload(ControlPlan.items))
            .where(ControlPlan.pfmea_project_id == pfmea_id)
        )
    ).first()


async def list_control_plans(
    db,
    skip=0,
    limit=50,
    search=None,
    status_filter=None,
    customers=None,
    sort="date-desc",
):
    statement = select(ControlPlan).join(
        PfmeaHeader, ControlPlan.pfmea_project_id == PfmeaHeader.id
    )
    if search:
        statement = statement.where(
            ControlPlan.title.ilike(f"%{search}%")
            | ControlPlan.control_plan_code.ilike(f"%{search}%")
            | PfmeaHeader.project_name.ilike(f"%{search}%")
            | PfmeaHeader.customer.ilike(f"%{search}%")
        )
    if status_filter:
        statement = statement.where(ControlPlan.status.in_(status_filter.split(",")))
    if customers:
        statement = statement.where(PfmeaHeader.customer.in_(customers.split(",")))
    ordering = {
        "date-desc": ControlPlan.created_at.desc(),
        "date-asc": ControlPlan.created_at.asc(),
        "title-asc": ControlPlan.title.asc(),
        "title-desc": ControlPlan.title.desc(),
    }.get(sort, ControlPlan.created_at.desc())
    # Execute count through ORM so the same scope criteria are applied.
    total = (
        await db.execute(statement.with_only_columns(func.count(ControlPlan.id)))
    ).scalar_one()
    items = (
        await db.scalars(
            statement.options(selectinload(ControlPlan.items))
            .order_by(ordering, ControlPlan.id.desc())
            .offset(skip)
            .limit(limit)
        )
    ).all()
    return {"items": items, "total": total, "skip": skip, "limit": limit}


async def create_control_plan_from_pfmea(db, pfmea_id, current_user_id, payload):
    pfmea = await db.get(PfmeaHeader, pfmea_id)
    if not pfmea:
        raise HTTPException(404, "PFMEA not found")
    if pfmea.moc_status != "Approved":
        raise HTTPException(400, "Control plans require an approved PFMEA")
    if await get_control_plan_by_pfmea(db, pfmea_id):
        raise HTTPException(409, "Control Plan already exists")
    cp = ControlPlan(
        pfmea_project_id=pfmea.id,
        flowchart_id=pfmea.flowchart_id,
        control_plan_code=f"CP-{pfmea.pfmea_id_number}",
        title=payload.title,
        owner_id=current_user_id,
        status="Draft",
        start_date=date.today(),
        created_by=current_user_id,
        observations=payload.observations,
    )
    db.add(cp)
    await db.flush()
    await sync_critical_items(db, cp.id, current_user_id)
    return await _get_control_plan_or_404(db, cp.id)


async def sync_critical_items(db, control_plan_id, current_user_id):
    cp = await _get_control_plan_or_404(db, control_plan_id)
    if cp.status in {"Approved", "Archived"}:
        raise HTTPException(403, "Approved or archived plan is immutable")
    rows = list(
        (
            await db.scalars(
                select(PfmeaWorksheetRow).where(
                    PfmeaWorksheetRow.pfmea_id == cp.pfmea_project_id
                )
            )
        ).all()
    )
    critical = {
        r.id: r for r in rows if r.action_priority == "H" or (r.severity or 0) >= 9
    }
    existing = {
        item.pfmea_worksheet_row_id: item
        for item in cp.items
        if item.pfmea_worksheet_row_id is not None
    }
    seq = max((i.item_sequence for i in cp.items), default=0) + 10
    for item in cp.items:
        item.needs_review = (
            item.pfmea_worksheet_row_id not in critical and not item.source_reviewed
        )
    for row_id, row in critical.items():
        name = f"Mode: {row.failure_mode} (Step: {row.station_operation})"
        item = existing.get(row_id)
        if item:
            item.item_name = name
            item.is_active = True
            item.source_reviewed = False
        else:
            item = ControlPlanItem(
                control_plan_id=cp.id,
                item_sequence=seq,
                item_name=name,
                pfmea_worksheet_row_id=row_id,
                source_row_id=row_id,
                characteristic=row.product_characteristic or row.process_characteristic,
                needs_review=False,
            )
            db.add(item)
            existing[row_id] = item
            seq += 10
    db.add(
        AuditLog(
            action="SYNC_CONTROL_PLAN",
            performed_by=current_user_id,
            control_plan_id=cp.id,
            entity_type="control_plan",
            entity_id=cp.id,
        )
    )
    await db.flush()
    await db.refresh(cp, attribute_names=["items"])
    return cp.items


async def update_control_plan_item(db, item_id, payload, current_user_id):
    item = await db.get(ControlPlanItem, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    cp = await _get_control_plan_or_404(db, item.control_plan_id)
    if cp.status in {"Approved", "Archived"}:
        raise HTTPException(403, "Approved or archived plan is immutable")
    data = payload.model_dump(exclude_unset=True)
    if "item_name" in data and not data["item_name"]:
        raise HTTPException(400, "Item name cannot be empty")
    if "item_sequence" in data and data["item_sequence"] is None:
        raise HTTPException(400, "Sequence cannot be empty")
    if data.get("responsible_person_id"):
        from app.models import User, PfmeaTeamMember

        person = await db.get(User, data["responsible_person_id"])
        assigned = (
            await db.scalars(
                select(PfmeaTeamMember).where(
                    PfmeaTeamMember.pfmea_id == cp.pfmea_project_id,
                    PfmeaTeamMember.user_id == data["responsible_person_id"],
                )
            )
        ).first()
        parent = await db.get(PfmeaHeader, cp.pfmea_project_id)
        if (
            not person
            or not person.is_active
            or person.deleted_at is not None
            or (not assigned and parent.owner_id != person.id)
        ):
            raise HTTPException(
                400, "Responsible person must be an active project member"
            )
    for key, value in data.items():
        setattr(item, key, value)
    await db.flush()
    return item


async def transition_control_plan(db, cp_id, new_status, actor_id):
    cp = await _get_control_plan_or_404(db, cp_id)
    allowed = {
        "Draft": ["In Review"],
        "In Review": ["Draft", "Approved"],
        "Approved": ["Archived"],
        "Archived": [],
    }
    if new_status not in allowed.get(cp.status, []):
        raise HTTPException(400, "Invalid control-plan transition")
    if new_status in {"In Review", "Approved"}:
        parent = await db.get(PfmeaHeader, cp.pfmea_project_id)
        if not parent or parent.moc_status != "Approved":
            raise HTTPException(400, "Source PFMEA must be approved")
        await sync_critical_items(db, cp.id, actor_id)
        if any(item.needs_review for item in cp.items):
            raise HTTPException(400, "Historical source links require explicit review")
        active = [item for item in cp.items if item.is_active]
        if not active or any(
            not all(
                (
                    i.characteristic,
                    i.classification,
                    i.specification,
                    i.measurement_method,
                    i.sample_size,
                    i.sample_frequency,
                    i.responsible_person_id,
                    i.reaction_plan,
                )
            )
            or i.needs_review
            for i in active
        ):
            raise HTTPException(
                400,
                "All controls require complete operational data and reviewed source links",
            )
    cp.status = new_status
    if new_status == "Approved":
        cp.last_revision_date = date.today()
        from app.schemas.control_plan import ControlPlanRead

        db.add(
            DocumentVersion(
                document_type="control_plan",
                document_id=cp.id,
                revision_number=cp.version,
                change_reason="Approved",
                created_by=actor_id,
                original_creation_date=cp.created_at,
                snapshot_data=ControlPlanRead.model_validate(cp).model_dump(
                    mode="json"
                ),
                is_initial_revision=False,
            )
        )
    cp.status = new_status
    cp.needs_review = False if new_status == "Approved" else cp.needs_review
    await db.flush()
    return cp


async def review_source(db, item_id, keep, reason, actor_id):
    item = await db.get(ControlPlanItem, item_id)
    if not item:
        raise HTTPException(404, "Control not found")
    cp = await _get_control_plan_or_404(db, item.control_plan_id)
    if cp.status in {"Approved", "Archived"}:
        raise HTTPException(403, "Approved plan is immutable")
    row = (
        await db.get(PfmeaWorksheetRow, item.pfmea_worksheet_row_id)
        if item.pfmea_worksheet_row_id
        else None
    )
    if not keep and row and (row.action_priority == "H" or (row.severity or 0) >= 9):
        raise HTTPException(400, "Controls for current high risks cannot be retired")
    item.source_reviewed = True
    item.source_review_reason = reason.strip()
    item.needs_review = False
    item.is_active = keep
    db.add(
        AuditLog(
            action="CONTROL_SOURCE_REVIEWED",
            performed_by=actor_id,
            control_plan_id=cp.id,
            entity_type="control_plan_item",
            entity_id=item.id,
            action_details=reason.strip(),
        )
    )
    await db.flush()
    return item


async def reopen_control_plan(db, cp_id, reason, actor_id):
    cp = await _get_control_plan_or_404(db, cp_id)
    if cp.status not in {"Approved", "Archived"}:
        raise HTTPException(400, "Only approved or archived plans can be reopened")
    from app.schemas.control_plan import ControlPlanRead

    db.add(
        DocumentVersion(
            document_type="control_plan",
            document_id=cp.id,
            revision_number=cp.version,
            change_reason=reason,
            created_by=actor_id,
            original_creation_date=cp.created_at,
            snapshot_data=ControlPlanRead.model_validate(cp).model_dump(mode="json"),
            is_initial_revision=False,
        )
    )
    cp.version += 1
    cp.status = "Draft"
    await sync_critical_items(db, cp.id, actor_id)
    await db.flush()
    return cp
