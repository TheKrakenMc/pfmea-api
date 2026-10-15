"""Defense in depth: every ORM read is scoped to the authenticated resource context."""

from sqlalchemy import event, or_, select
from sqlalchemy.orm import Session, with_loader_criteria
from app.models import (
    Base,
    PfmeaHeader,
    PfmeaTeamMember,
    Flowchart,
    ControlPlan,
    ControlPlanItem,
    PfmeaWorksheetRow,
    Plant,
)


@event.listens_for(Session, "do_orm_execute")
def scope_reads(state):
    info = state.session.info
    if not state.is_select or "current_user_id" not in info:
        return
    uid, plant, role = (
        info["current_user_id"],
        info.get("plant_id"),
        info.get("role_name"),
    )
    statement = state.statement
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, "plant_id") and model.__tablename__ not in {
            "users",
            "plants",
        }:
            statement = statement.options(
                with_loader_criteria(
                    model,
                    or_(model.plant_id == plant, model.plant_id.is_(None)),
                    include_aliases=True,
                )
            )
    from app.models import Product, ProductParameter

    product_ids = select(Product.id).where(
        or_(Product.plant_id == plant, Product.plant_id.is_(None))
    )
    statement = statement.options(
        with_loader_criteria(
            ProductParameter,
            ProductParameter.product_id.in_(product_ids),
            include_aliases=True,
        )
    )
    if role == "administrator":
        state.statement = statement
        return
    statement = statement.options(
        with_loader_criteria(
            Plant, Plant.id.in_(info.get("plant_ids", [])), include_aliases=True
        )
    )
    member_ids = select(PfmeaTeamMember.pfmea_id).where(PfmeaTeamMember.user_id == uid)
    pfmea_ids = select(PfmeaHeader.id).where(
        or_(PfmeaHeader.owner_id == uid, PfmeaHeader.id.in_(member_ids)),
        PfmeaHeader.plant_id == plant,
    )
    statement = statement.options(
        with_loader_criteria(
            PfmeaHeader,
            or_(PfmeaHeader.owner_id == uid, PfmeaHeader.id.in_(member_ids)),
            include_aliases=True,
        )
    )
    statement = statement.options(
        with_loader_criteria(
            PfmeaWorksheetRow,
            PfmeaWorksheetRow.pfmea_id.in_(pfmea_ids),
            include_aliases=True,
        )
    )
    statement = statement.options(
        with_loader_criteria(
            ControlPlan,
            ControlPlan.pfmea_project_id.in_(pfmea_ids),
            include_aliases=True,
        )
    )
    cp_ids = select(ControlPlan.id).where(ControlPlan.pfmea_project_id.in_(pfmea_ids))
    statement = statement.options(
        with_loader_criteria(
            ControlPlanItem,
            ControlPlanItem.control_plan_id.in_(cp_ids),
            include_aliases=True,
        )
    )
    if role != "process engineer":
        fc_ids = select(PfmeaHeader.flowchart_id).where(PfmeaHeader.id.in_(pfmea_ids))
        statement = statement.options(
            with_loader_criteria(
                Flowchart,
                or_(Flowchart.created_by == uid, Flowchart.id.in_(fc_ids)),
                include_aliases=True,
            )
        )
    state.statement = statement
