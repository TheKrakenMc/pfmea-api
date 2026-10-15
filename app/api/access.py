"""Resource authorization shared by all private routers."""

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, CurrentUser
from app.core.db import get_db
from app.models import (
    PfmeaHeader,
    PfmeaTeamMember,
    Flowchart,
    ControlPlan,
    ControlPlanItem,
    DocumentVersion,
)


async def check_pfmea(db, user, pfmea_id, write=False, manage=False):
    doc = await db.get(PfmeaHeader, pfmea_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if user.role_name.lower() == "administrator":
        return doc
    if doc.plant_id not in user.plant_ids or doc.plant_id != user.plant_id:
        raise HTTPException(403, "Plant access denied")
    membership = (
        await db.scalars(
            select(PfmeaTeamMember).where(
                PfmeaTeamMember.pfmea_id == pfmea_id, PfmeaTeamMember.user_id == user.id
            )
        )
    ).first()
    owner = doc.owner_id == user.id or (
        membership and membership.role_in_team == "PFMEA Owner"
    )
    if not owner and not membership:
        raise HTTPException(403, "Project access denied")
    role = user.role_name.lower()
    if write and (
        role not in {"pfmea owner", "team member"}
        or (membership and membership.role_in_team == "Viewer")
    ):
        raise HTTPException(403, "Read-only access")
    if manage and (role != "pfmea owner" or not owner):
        raise HTTPException(403, "Project owner required")
    return doc


async def check_flowchart(db, user, flowchart_id, write=False):
    doc = await db.get(Flowchart, flowchart_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if user.role_name.lower() == "administrator":
        return doc
    if doc.plant_id not in user.plant_ids or doc.plant_id != user.plant_id:
        raise HTTPException(403, "Plant access denied")
    assigned = (
        await db.scalars(
            select(PfmeaHeader.id)
            .outerjoin(PfmeaTeamMember)
            .where(
                PfmeaHeader.flowchart_id == flowchart_id,
                or_(
                    PfmeaHeader.owner_id == user.id, PfmeaTeamMember.user_id == user.id
                ),
            )
        )
    ).first()
    owner_id = getattr(doc, "created_by", None)
    if (
        user.role_name.lower() != "process engineer"
        and not assigned
        and owner_id != user.id
    ):
        raise HTTPException(403, "Project access denied")
    if write and user.role_name.lower() != "process engineer" and owner_id != user.id:
        writable = (
            await db.scalars(
                select(PfmeaHeader.id)
                .outerjoin(PfmeaTeamMember)
                .where(
                    PfmeaHeader.flowchart_id == flowchart_id,
                    or_(
                        PfmeaHeader.owner_id == user.id,
                        (PfmeaTeamMember.user_id == user.id)
                        & (PfmeaTeamMember.role_in_team != "Viewer"),
                    ),
                )
            )
        ).first()
        if not writable:
            raise HTTPException(403, "Project membership is read-only")
    if write and user.role_name.lower() not in {
        "administrator",
        "pfmea owner",
        "team member",
        "process engineer",
    }:
        raise HTTPException(403, "Read-only access")
    return doc


async def authorize_request(
    request: Request,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    write = request.method not in {"GET", "HEAD", "OPTIONS"}
    role = user.role_name.lower()
    if write and role == "viewer":
        raise HTTPException(403, "Read-only access")
    if role not in {
        "administrator",
        "pfmea owner",
        "team member",
        "viewer",
        "process engineer",
    }:
        raise HTTPException(403, "Unknown role")
    if (
        write
        and role == "process engineer"
        and not request.url.path.startswith("/api/v1/flowcharts")
    ):
        raise HTTPException(403, "Process engineers may modify diagrams only")
    if (
        request.method == "DELETE"
        and role != "administrator"
        and not any(
            part in request.url.path
            for part in ("/pfmea-project/", "/flowcharts/", "/control-plans/")
        )
    ):
        raise HTTPException(403, "Administrator required for catalog deletion")
    if (
        write
        and any(
            request.url.path.startswith("/api/v1/" + name)
            for name in (
                "plants",
                "departments",
                "technology-categories",
                "measurement-units",
            )
        )
        and role != "administrator"
    ):
        raise HTTPException(403, "Administrator required for shared catalog changes")
    params = request.path_params
    path = request.url.path
    body = None
    if write and request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()
        except ValueError:
            raise HTTPException(400, "Invalid JSON")
    if isinstance(body, dict) and role != "administrator":
        if body.get("plant_id") is not None and body["plant_id"] != user.plant_id:
            raise HTTPException(403, "Plant access denied")
        for field in ("created_by", "owner_id", "performed_by"):
            if body.get(field) is not None and body[field] != user.id:
                raise HTTPException(403, "Actor cannot be supplied by the client")
    if (
        "plant_id" in params
        and role != "administrator"
        and int(params["plant_id"]) not in user.plant_ids
    ):
        raise HTTPException(403, "Plant access denied")
    from app.models import Product, ProductParameter, Technology, TechnologyParameter

    if "product_id" in params:
        if not await db.get(Product, int(params["product_id"])):
            raise HTTPException(404, "Product not found")
    if "tech_id" in params:
        if not await db.get(Technology, int(params["tech_id"])):
            raise HTTPException(404, "Technology not found")
    if "param_id" in params:
        model = ProductParameter if "/products/" in path else TechnologyParameter
        if not await db.get(model, int(params["param_id"])):
            raise HTTPException(404, "Parameter not found")
    document = None
    if "product_id" in params:
        document = await db.get(Product, int(params["product_id"]))
    elif "param_id" in params and "/products/" in path:
        parameter = await db.get(ProductParameter, int(params["param_id"]))
        document = await db.get(Product, parameter.product_id)
    if "pfmea_id" in params and "/control-plans/project/" in path and not write:
        await check_pfmea(db, user, int(params["pfmea_id"]))
        document = (
            await db.scalars(
                select(ControlPlan).where(
                    ControlPlan.pfmea_project_id == int(params["pfmea_id"])
                )
            )
        ).first()
    elif "pfmea_id" in params:
        document = await check_pfmea(
            db,
            user,
            int(params["pfmea_id"]),
            write,
            write
            and any(
                part in path
                for part in ("/status", "/restore", "/team", "/confirm-action")
            ),
        )
    elif "control_plan_id" in params or (
        "/control-plans/items/" in path and "item_id" in params
    ):
        cp_id = params.get("control_plan_id")
        if cp_id is None:
            item = await db.get(ControlPlanItem, int(params["item_id"]))
            if not item:
                raise HTTPException(404, "Item not found")
            cp_id = item.control_plan_id
        document = await db.get(ControlPlan, int(cp_id))
        if not document:
            raise HTTPException(404, "Plan not found")
        await check_pfmea(
            db,
            user,
            document.pfmea_project_id,
            write,
            write and path.endswith(("/status", "/review-source", "/restore")),
        )
    elif "flowchart_id" in params:
        document = await check_flowchart(db, user, int(params["flowchart_id"]), write)
        requested = (
            (body or {}).get("status") or (body or {}).get("header", {}).get("status")
            if isinstance(body, dict)
            else None
        )
        managing = path.endswith(("/archive", "/restore")) or (
            requested and requested.lower() in {"approved", "archived"}
        )
        if write and managing and role != "administrator":
            owned = (
                await db.scalars(
                    select(PfmeaHeader.id).where(
                        PfmeaHeader.flowchart_id == document.id,
                        PfmeaHeader.owner_id == user.id,
                    )
                )
            ).first()
            if role != "pfmea owner" or (document.created_by != user.id and not owned):
                raise HTTPException(403, "Document owner required")
    elif (
        "version_id" in params
        or "document_id" in params
        or "/document-versions" in path
    ):
        if "version_id" in params:
            version = await db.get(DocumentVersion, int(params["version_id"]))
            if not version:
                raise HTTPException(404, "Version not found")
            kind, doc_id = version.document_type, version.document_id
        else:
            kind = params.get("document_type") or (body or {}).get("document_type")
            doc_id = params.get("document_id") or (body or {}).get("document_id")
        if kind == "product":
            document = await db.get(Product, int(doc_id))
            if not document:
                raise HTTPException(404, "Product not found")
        elif kind in {"pfmea", "pfmea_project"}:
            document = await check_pfmea(db, user, int(doc_id), write, write)
        elif kind == "flowchart":
            document = await check_flowchart(db, user, int(doc_id), write)
        elif kind == "control_plan":
            document = await db.get(ControlPlan, int(doc_id))
            if not document:
                raise HTTPException(404, "Plan not found")
            await check_pfmea(db, user, document.pfmea_project_id, write, write)
        else:
            raise HTTPException(400, "Unsupported document type")
        if isinstance(body, dict):
            body["created_by"] = user.id
    if write and isinstance(body, dict) and body.get("flowchart_id"):
        await check_flowchart(db, user, int(body["flowchart_id"]))
    if document is not None and hasattr(document, "lock_version"):
        key = f"{document.__tablename__}:{document.id}"
        if write:
            if (
                isinstance(body, dict)
                and (body.get("status") or (body.get("header") or {}).get("status"))
                in {"Approved", "Released", "Archived"}
                and role not in {"administrator", "pfmea owner"}
            ):
                raise HTTPException(403, "Owner approval required")
            lifecycle = path.endswith(("/status", "/restore", "/archive", "/revisions")) or (request.method=="POST" and "/control-plans/project/" in path)
            if (
                getattr(document, "moc_status", getattr(document, "status", None))
                in {"Approved", "Archived"}
                and not lifecycle
            ):
                raise HTTPException(403, "Approved or archived documents are immutable")
            expected = (
                body.get("expected_version") if isinstance(body, dict) else None
            ) or request.headers.get("if-match")
            if expected is None:
                raise HTTPException(428, "Document revision required")
            try:
                expected = int(str(expected).strip('"'))
            except ValueError:
                raise HTTPException(400, "Invalid document revision")
            model = type(document)
            locked = (
                await db.scalars(
                    select(model)
                    .where(model.id == document.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            ).first()
            if locked is None:
                raise HTTPException(404, "Document no longer accessible")
            if (
                getattr(locked, "moc_status", getattr(locked, "status", None))
                in {"Approved", "Released", "Archived"}
                and not lifecycle
            ):
                raise HTTPException(403, "Approved or archived documents are immutable")
            if isinstance(locked, PfmeaHeader):
                await check_pfmea(db, user, locked.id, True, False)
            if locked.lock_version != expected:
                raise HTTPException(409, "Document changed; reload before saving")
            locked.lock_version += 1
            await db.flush()
            document = locked
        response.headers["X-Document-Key"] = key
        response.headers["X-Document-Version"] = str(document.lock_version)
    return user
