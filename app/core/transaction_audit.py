"""Field changes and their audit evidence commit together."""

from sqlalchemy import event, inspect, select
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def resource_links(obj):
    table = inspect(obj).mapper.local_table.name
    if table == "pfmea_headers":
        return {"pfmea_project_id": obj.id}
    if table in {"pfmea_worksheet_rows", "pfmea_team_members"}:
        return {"pfmea_project_id": obj.pfmea_id}
    if table == "flowcharts":
        return {"flowchart_id": obj.id}
    if table == "flowchart_steps":
        return {"flowchart_id": obj.flowchart_id}
    if table == "control_plans":
        return {"control_plan_id": obj.id}
    if table in {"control_plan_items"}:
        return {"control_plan_id": obj.control_plan_id}
    return {}


SECRET_FIELDS = {"password_hash", "refresh_hash", "csrf_token", "otp_code"}
EXCLUDED = {
    "auth_sessions",
    "used_verification_tokens",
    "document_audit_logs",
    "user_otps",
}


@event.listens_for(Session, "before_flush")
def audit_changes(session, flush_context, instances):
    actor = session.info.get("current_user_id")
    if not actor:
        return
    session.info.setdefault("audit_new", []).extend(
        obj
        for obj in session.new
        if inspect(obj).mapper.local_table.name not in EXCLUDED
    )
    from fastapi import HTTPException

    for obj in list(session.new) + list(session.dirty):
        state = inspect(obj)
        if state.mapper.local_table.name in EXCLUDED:
            continue
        role = session.info.get("role_name")
        plant = session.info.get("plant_id")
        if hasattr(obj, "plant_id") and state.mapper.local_table.name not in {
            "users",
            "plants",
        }:
            if obj in session.new and obj.plant_id is None:
                obj.plant_id = plant
            if role != "administrator" and obj.plant_id != plant:
                raise HTTPException(403, "Plant assignment cannot be changed")
        if hasattr(obj, "created_by") and obj in session.new:
            obj.created_by = actor
        for column in state.mapper.columns:
            value = getattr(obj, column.key, None)
            if value is None:
                continue
            for fk in column.foreign_keys:
                table = fk.column.table
                cache = session.info.setdefault("validated_foreign_keys", {})
                cache_key = (table.name, fk.column.name, value)
                if cache_key in cache:
                    target_plant = cache[cache_key]
                else:
                    scoped = "plant_id" in table.c and table.name not in {
                        "users",
                        "plants",
                    }
                    selected = table.c.plant_id if scoped else fk.column
                    target = (
                        session.connection()
                        .execute(select(selected).where(fk.column == value))
                        .first()
                    )
                    if target is None:
                        raise HTTPException(400, "Referenced resource does not exist")
                    target_plant = target[0] if scoped else None
                    cache[cache_key] = target_plant
                if role != "administrator" and target_plant not in {None, plant}:
                    raise HTTPException(
                        403, "Referenced resource is outside the authorized plant"
                    )
    from app.models import PfmeaWorksheetRow, ControlPlanItem, ControlPlan

    for removed in list(session.deleted):
        if isinstance(removed, PfmeaWorksheetRow):
            items = session.scalars(
                select(ControlPlanItem).where(
                    ControlPlanItem.pfmea_worksheet_row_id == removed.id
                )
            ).all()
            for item in items:
                item.source_row_id = removed.id
                item.pfmea_worksheet_row_id = None
                item.needs_review = True
                plan = session.get(ControlPlan, item.control_plan_id)
                if plan:
                    plan.needs_review = True
    for obj in list(session.dirty) + list(session.deleted):
        state = inspect(obj)
        if state.mapper.local_table.name in EXCLUDED:
            continue
        for column in state.mapper.columns:
            if column.key in SECRET_FIELDS:
                continue
            history = state.attrs[column.key].history
            if not history.has_changes() and obj not in session.deleted:
                continue
            old = history.deleted[0] if history.deleted else None
            new = history.added[0] if history.added else None
            session.add(
                AuditLog(
                    **resource_links(obj),
                    action="DELETE" if obj in session.deleted else "UPDATE",
                    performed_by=actor,
                    entity_type=state.mapper.local_table.name,
                    entity_id=getattr(obj, "id", None),
                    field_name=column.key,
                    old_value=str(old) if old is not None else None,
                    new_value=str(new) if new is not None else None,
                )
            )


@event.listens_for(Session, "after_flush_postexec")
def audit_insertions(session, flush_context):
    actor = session.info.get("current_user_id")
    for obj in session.info.pop("audit_new", []):
        state = inspect(obj)
        values = {
            column.key: str(getattr(obj, column.key))
            for column in state.mapper.columns
            if column.key not in SECRET_FIELDS
            and getattr(obj, column.key, None) is not None
        }
        session.add(
            AuditLog(
                **resource_links(obj),
                action="CREATE",
                performed_by=actor,
                entity_type=state.mapper.local_table.name,
                entity_id=getattr(obj, "id", None),
                new_values=values,
            )
        )
