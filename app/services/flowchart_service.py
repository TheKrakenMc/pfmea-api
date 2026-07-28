"""Service layer for Flowchart & FlowchartStep business logic.

All database interactions for the *Structure Analysis* module
(AIAG-VDA Step 2) live here, keeping routers thin.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.audit_log import AuditLog
from app.models.document_version import DocumentVersion
from app.models.flowchart import Flowchart
from app.models.flowchart_step import FlowchartStep
from app.models.product import Product
from app.models.technology import Technology
from app.models.machinery import Machinery
from app.models.customer import Customer
from app.models.pfmea_header import PfmeaHeader
from app.models.pfmea_team_member import PfmeaTeamMember
from app.models.user import User
from app.schemas.flowchart import FlowchartCreate, FlowchartStepCreate, FlowchartUpdate, ProductCreate


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


async def _ensure_machinery_exists(db: AsyncSession, machinery_id: int) -> None:
    """Raise 404 if the referenced machinery does not exist."""
    result = await db.execute(
        select(Machinery.id).where(Machinery.id == machinery_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Maquinaria con id {machinery_id} no encontrada.",
        )


async def _ensure_flowchart_exists(
    db: AsyncSession, flowchart_id: int
) -> Flowchart:
    """Return the flowchart or raise 404."""
    result = await db.execute(
        select(Flowchart)
        .options(
            joinedload(Flowchart.steps).joinedload(FlowchartStep.technology).selectinload(Technology.parameters),
            joinedload(Flowchart.steps).joinedload(FlowchartStep.machinery),
            joinedload(Flowchart.product).joinedload(Product.customer),
        )
        .where(Flowchart.id == flowchart_id)
    )
    flowchart = result.unique().scalar_one_or_none()
    if flowchart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagrama de flujo con id {flowchart_id} no encontrado.",
        )
    return flowchart


async def _get_or_create_customer(db: AsyncSession, company_name: str, plant_id: int) -> Customer:
    """Find an existing customer by name and plant, or create a new one to preserve integrity."""
    stmt = select(Customer).where(
        Customer.company_name == company_name,
        Customer.plant_id == plant_id
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()
    if customer:
        return customer

    # Generate customer_code from company_name
    clean_name = "".join(c for c in company_name if c.isalnum()).upper()
    if not clean_name:
        clean_name = "GENERIC"
    customer_code = f"CUST-{clean_name}"

    # Check uniqueness of customer_code
    code_stmt = select(Customer).where(Customer.customer_code == customer_code)
    existing_code = (await db.execute(code_stmt)).scalar_one_or_none()
    if existing_code:
        import uuid
        customer_code = f"{customer_code}-{str(uuid.uuid4())[:4].upper()}"

    customer = Customer(
        plant_id=plant_id,
        customer_code=customer_code,
        company_name=company_name,
        status="active",
        is_active=True
    )
    db.add(customer)
    await db.flush()
    return customer


async def _generate_hierarchical_id(
    db: AsyncSession, plant_id: int | None, version: int = 1
) -> str:
    """Generate the hierarchical ID pattern: [PLANT_CODE]_FC_[SEQ]_[YEAR]_[VERSION]."""
    from datetime import datetime, timezone
    from sqlalchemy import func
    from app.models.plant import Plant

    plant_code = "PLANT"
    if plant_id:
        result = await db.execute(select(Plant.code).where(Plant.id == plant_id))
        code = result.scalar_one_or_none()
        if code:
            plant_code = code.upper().replace(" ", "_")

    year = datetime.now(timezone.utc).year

    # Get next sequence number for this plant
    result = await db.execute(
        select(func.count(Flowchart.id)).where(Flowchart.plant_id == plant_id)
    )
    seq = (result.scalar() or 0) + 1

    return f"{plant_code}_FLOWCHART_{seq:03d}_{year}_{version}"


# ---------------------------------------------------------------------------
# Flowchart CRUD
# ---------------------------------------------------------------------------

async def create_flowchart(
    db: AsyncSession,
    payload: FlowchartCreate,
    current_user_id: int,
) -> Flowchart:
    """Create a flowchart with optional inline steps.

    Validates:
    - ``product_id`` exists.
    - Every ``technology_id`` referenced in steps exists.
    - ``step_number`` values are unique within the batch.
    """
    # 1) Validate FK references and get product plant_id and technologies
    stmt = (
        select(Product)
        .options(selectinload(Product.technologies))
        .where(Product.id == payload.product_id)
    )
    res = await db.execute(stmt)
    product = res.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con id {payload.product_id} no encontrado.",
        )
    plant_id = product.plant_id

    # 2) Validate step-number uniqueness within the request payload
    step_numbers = [s.step_number for s in payload.steps]
    if len(step_numbers) != len(set(step_numbers)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Números de paso duplicados en la solicitud.",
        )

    # 3) Validate every referenced technology and machinery
    for step_data in payload.steps:
        if step_data.technology_id is not None:
            await _ensure_technology_exists(db, step_data.technology_id)
        if step_data.machinery_id is not None:
            await _ensure_machinery_exists(db, step_data.machinery_id)

    # 4) Build the ORM graph
    flowchart_code = await _generate_hierarchical_id(db, plant_id)

    flowchart = Flowchart(
        plant_id=plant_id,
        product_id=payload.product_id,
        owner_id=payload.owner_id,
        flowchart_code=flowchart_code,
        title=payload.title,
        status=payload.status,
        created_by=current_user_id,
    )
    if not payload.steps and product.technologies:
        step_num = 10
        for tech in product.technologies:
            flowchart.steps.append(
                FlowchartStep(
                    technology_id=tech.id,
                    machinery_id=None,
                    step_number=step_num,
                    responsible_department="Producción",
                    symbol_type="operation",
                    custom_description=None,
                    critical_flag="none",
                )
            )
            step_num += 10
    else:
        for step_data in payload.steps:
            flowchart.steps.append(
                FlowchartStep(
                    technology_id=step_data.technology_id,
                    machinery_id=step_data.machinery_id,
                    step_number=step_data.step_number,
                    responsible_department=step_data.responsible_department,
                    symbol_type=step_data.symbol_type,
                    custom_description=step_data.custom_description,
                    critical_flag=step_data.critical_flag,
                )
            )

    db.add(flowchart)
    await db.flush()          # assign PKs without committing
    return await _ensure_flowchart_exists(db, flowchart.id)


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
        .options(
            joinedload(Flowchart.product).joinedload(Product.customer),
            joinedload(Flowchart.steps).joinedload(FlowchartStep.technology).selectinload(Technology.parameters),
            joinedload(Flowchart.steps).joinedload(FlowchartStep.machinery),
        )
        .order_by(Flowchart.id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.unique().scalars().all())


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

    # 2) Validate technology and machinery FK
    if payload.technology_id is not None:
        await _ensure_technology_exists(db, payload.technology_id)
    if payload.machinery_id is not None:
        await _ensure_machinery_exists(db, payload.machinery_id)

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
        machinery_id=payload.machinery_id,
        step_number=payload.step_number,
        responsible_department=payload.responsible_department,
        symbol_type=payload.symbol_type,
        custom_description=payload.custom_description,
        critical_flag=payload.critical_flag,
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


async def replace_steps(
    db: AsyncSession,
    flowchart_id: int,
    steps_data: list[FlowchartStepCreate],
) -> Flowchart:
    """Atomically replace all steps for a flowchart with the given ordered list.

    Used by the frontend auto-save after drag-and-drop reordering.

    Validates:
    - ``flowchart_id`` exists.
    - ``step_number`` values are unique within the batch.
    - Every ``technology_id`` referenced exists.
    """
    # 1) Validate parent flowchart
    flowchart = await _ensure_flowchart_exists(db, flowchart_id)

    # 2) Validate step-number uniqueness within the request payload
    step_numbers = [s.step_number for s in steps_data]
    if len(step_numbers) != len(set(step_numbers)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Números de paso duplicados en la solicitud.",
        )

    # 3) Validate every referenced technology and machinery
    for step_data in steps_data:
        if step_data.technology_id is not None:
            await _ensure_technology_exists(db, step_data.technology_id)
        if step_data.machinery_id is not None:
            await _ensure_machinery_exists(db, step_data.machinery_id)

    # 4) Delete existing steps
    from sqlalchemy import delete

    await db.execute(
        delete(FlowchartStep).where(FlowchartStep.flowchart_id == flowchart_id)
    )

    # 5) Insert new steps in order
    for step_data in steps_data:
        db.add(
            FlowchartStep(
                flowchart_id=flowchart_id,
                technology_id=step_data.technology_id,
                machinery_id=step_data.machinery_id,
                step_number=step_data.step_number,
                responsible_department=step_data.responsible_department,
                symbol_type=step_data.symbol_type,
                custom_description=step_data.custom_description,
                critical_flag=step_data.critical_flag,
            )
        )

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflicto de integridad al reemplazar pasos en el flujo {flowchart_id}.",
        )

    # 6) Refresh and return the flowchart with new steps
    await db.refresh(flowchart)
    # Re-fetch with eager loading
    return await _ensure_flowchart_exists(db, flowchart_id)


# ---------------------------------------------------------------------------
# Metadata & Product Updates
# ---------------------------------------------------------------------------

async def update_flowchart(
    db: AsyncSession,
    flowchart_id: int,
    payload: FlowchartUpdate,
) -> Flowchart:
    """Update flowchart title, status and nested product properties."""
    flowchart = await _ensure_flowchart_exists(db, flowchart_id)

    if payload.title is not None:
        flowchart.title = payload.title
    if payload.status is not None:
        flowchart.status = payload.status

    if flowchart.product:
        if payload.customer_name is not None:
            customer = await _get_or_create_customer(db, payload.customer_name, flowchart.product.plant_id)
            flowchart.product.customer_id = customer.id
            flowchart.product.customer = customer
        if payload.part_number is not None:
            # Check unique constraint proactively if part number changed
            if payload.part_number != flowchart.product.part_number:
                stmt = select(Product).where(
                    Product.part_number == payload.part_number,
                    Product.plant_id == flowchart.product.plant_id
                )
                existing = (await db.execute(stmt)).scalar_one_or_none()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Ya existe un producto con el número de parte {payload.part_number}.",
                    )
            flowchart.product.part_number = payload.part_number
        if payload.product_description is not None:
            flowchart.product.description = payload.product_description

    db.add(flowchart)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al guardar la cabecera del diagrama.",
        )

    await db.refresh(flowchart)
    return await _ensure_flowchart_exists(db, flowchart_id)


async def list_products(db: AsyncSession) -> list[Product]:
    """Retrieve all master products for project creation selector."""
    result = await db.execute(
        select(Product)
        .options(joinedload(Product.customer))
        .order_by(Product.id)
    )
    return list(result.scalars().all())


async def create_product(db: AsyncSession, payload: ProductCreate) -> Product:
    """Create a new product record."""
    plant_id = payload.plant_id or 1
    # Check uniqueness
    stmt = select(Product).where(
        Product.part_number == payload.part_number,
        Product.plant_id == plant_id
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un producto con el número de parte {payload.part_number} en la planta.",
        )

    customer = await _get_or_create_customer(db, payload.customer_name, plant_id)

    product = Product(
        plant_id=plant_id,
        customer_id=customer.id,
        part_number=payload.part_number,
        description=payload.description,
    )
    product.customer = customer
    db.add(product)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al guardar el producto.",
        )

    await db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# Archive Flowchart
# ---------------------------------------------------------------------------

async def archive_flowchart(
    db: AsyncSession,
    flowchart_id: int,
    user_id: int,
    change_reason: str,
    eco_number: Optional[str] = None,
    lang: str = "es",
) -> Flowchart:
    """Archive a flowchart: update status, create DocumentVersion snapshot,
    insert AuditLog entry, and notify linked PFMEA team members via email.

    This function is the single point of truth for the archiving lifecycle event.
    All three DB writes happen in the same transaction (autocommit by middleware).
    """
    # 1) Fetch flowchart
    flowchart = await _ensure_flowchart_exists(db, flowchart_id)

    if flowchart.status and flowchart.status.lower() == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El diagrama de flujo ya está archivado.",
        )

    # 2) Fetch user details for audit + email
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    user_name = user.full_name if user else f"User #{user_id}"

    archived_at = datetime.now(timezone.utc)
    archived_at_str = archived_at.strftime("%Y-%m-%d %H:%M UTC")

    # 3) Build snapshot of current state
    snapshot = {
        "id": flowchart.id,
        "title": flowchart.title,
        "status": flowchart.status,
        "version": flowchart.version,
        "flowchart_code": flowchart.flowchart_code,
        "product_id": flowchart.product_id,
        "owner_id": flowchart.owner_id,
        "created_at": flowchart.created_at.isoformat() if flowchart.created_at else None,
        "steps_count": len(flowchart.steps),
        "archived_by_user_id": user_id,
        "archived_by_name": user_name,
        "change_reason": change_reason,
        "eco_number": eco_number,
    }

    # 4) Get current max revision for this document
    rev_result = await db.execute(
        select(DocumentVersion)
        .where(
            DocumentVersion.document_type == "flowchart",
            DocumentVersion.document_id == flowchart_id,
        )
        .order_by(DocumentVersion.revision_number.desc())
        .limit(1)
    )
    last_version = rev_result.scalar_one_or_none()
    next_revision = (last_version.revision_number + 1) if last_version else 1

    # 5) Create DocumentVersion record
    orig_date = flowchart.created_at or archived_at
    if orig_date.tzinfo is not None:
        orig_date = orig_date.replace(tzinfo=None)

    doc_version = DocumentVersion(
        document_type="flowchart",
        document_id=flowchart_id,
        revision_number=next_revision,
        change_reason=(
            f"[ECO: {eco_number}] {change_reason}" if eco_number else change_reason
        ),
        created_by=user_id,
        original_creation_date=orig_date,
        observations=f"Documento archivado el {archived_at_str} por {user_name}",
        snapshot_data=snapshot,
        is_initial_revision=(next_revision == 1),
    )
    db.add(doc_version)

    # 6) Create AuditLog record
    audit = AuditLog(
        flowchart_id=flowchart_id,
        action="ARCHIVED",
        performed_by=user_id,
        action_details=(
            f"Archivado por {user_name}. Razón: {change_reason}"
            + (f". ECO: {eco_number}" if eco_number else "")
        ),
        previous_values={"status": flowchart.status, "is_active": True},
        new_values={"status": "Archived", "is_active": False},
        entity_type="flowchart",
        entity_id=flowchart_id,
        field_name="status",
        old_value=flowchart.status,
        new_value="Archived",
    )
    db.add(audit)

    # 7) Update flowchart status
    flowchart.status = "Archived"
    flowchart.is_active = False
    db.add(flowchart)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error de integridad al archivar el diagrama de flujo.",
        )

    # 8) Send email notifications to PFMEA team members linked to this flowchart
    # Fire-and-forget: errors are logged but do NOT roll back the archiving
    try:
        from app.services.notification import send_archive_notification_email

        # Find linked PFMEA documents and their team members
        pfmea_result = await db.execute(
            select(PfmeaHeader)
            .options(joinedload(PfmeaHeader.team_members).joinedload(PfmeaTeamMember.user))
            .where(PfmeaHeader.flowchart_id == flowchart_id)
        )
        pfmea_headers = list(pfmea_result.unique().scalars().all())

        team_emails: list[tuple[str, str]] = []
        seen_emails: set[str] = set()

        for pfmea in pfmea_headers:
            for member in pfmea.team_members:
                if member.user and member.user.email and member.user.email not in seen_emails:
                    seen_emails.add(member.user.email)
                    team_emails.append((member.user.email, member.user.full_name or ""))

        # Also notify the flowchart owner if not already included
        if flowchart.owner and flowchart.owner.email and flowchart.owner.email not in seen_emails:
            team_emails.append((flowchart.owner.email, flowchart.owner.full_name or ""))

        if team_emails:
            import asyncio
            asyncio.create_task(
                send_archive_notification_email(
                    team_emails=team_emails,
                    doc_title=flowchart.title or f"Flowchart #{flowchart_id}",
                    doc_code=flowchart.flowchart_code or f"FC-{flowchart_id}",
                    doc_version=flowchart.version,
                    archived_by=user_name,
                    archived_at=archived_at_str,
                    change_reason=change_reason,
                    eco_number=eco_number,
                    lang=lang,
                )
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"Archive email notification failed for flowchart {flowchart_id}: {e}"
        )

    # 9) Return updated flowchart
    return await _ensure_flowchart_exists(db, flowchart_id)


# ---------------------------------------------------------------------------
# Flowchart History
# ---------------------------------------------------------------------------

async def get_flowchart_history(
    db: AsyncSession,
    flowchart_id: int,
) -> dict:
    """Retrieve document versions and audit log entries for a flowchart.
    Returns a dict with 'versions' and 'audit_logs' lists.
    """
    # Verify flowchart exists
    await _ensure_flowchart_exists(db, flowchart_id)

    # Fetch document versions with creator info
    versions_result = await db.execute(
        select(DocumentVersion)
        .options(joinedload(DocumentVersion.creator))
        .where(
            DocumentVersion.document_type == "flowchart",
            DocumentVersion.document_id == flowchart_id,
        )
        .order_by(DocumentVersion.created_at.asc())
    )
    versions = list(versions_result.unique().scalars().all())

    # Fetch audit log entries with performer info
    audit_result = await db.execute(
        select(AuditLog)
        .options(joinedload(AuditLog.performer))
        .where(AuditLog.flowchart_id == flowchart_id)
        .order_by(AuditLog.performed_at.asc())
    )
    audit_logs = list(audit_result.unique().scalars().all())

    return {
        "flowchart_id": flowchart_id,
        "versions": versions,
        "audit_logs": audit_logs,
    }
