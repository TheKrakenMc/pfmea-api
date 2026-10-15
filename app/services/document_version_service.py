"""Service layer for DocumentVersion business logic."""

from __future__ import annotations
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document_version import DocumentVersion
from app.schemas.document_version import DocumentVersionCreate


async def create_document_version(
    db: AsyncSession,
    payload: DocumentVersionCreate,
) -> DocumentVersion:
    """Create a new document version record."""
    from app.models import Product, Flowchart, PfmeaHeader, ControlPlan
    from app.schemas.product import ProductDetailRead
    from app.schemas.flowchart import FlowchartRead
    from app.schemas.pfmea import PfmeaHeaderDetailRead
    from app.schemas.control_plan import ControlPlanRead

    definitions = {
        "product": (Product, ProductDetailRead),
        "flowchart": (Flowchart, FlowchartRead),
        "pfmea": (PfmeaHeader, PfmeaHeaderDetailRead),
        "pfmea_project": (PfmeaHeader, PfmeaHeaderDetailRead),
        "control_plan": (ControlPlan, ControlPlanRead),
    }
    model, schema = definitions[payload.document_type]
    document = await db.get(model, payload.document_id)
    # Explicitly load relationships rather than trusting client-supplied historical content.
    relationships = [rel.key for rel in model.__mapper__.relationships]
    if relationships:
        await db.refresh(document, attribute_names=relationships)
    snapshot = schema.model_validate(document).model_dump(mode="json")
    version = DocumentVersion(
        document_type=payload.document_type,
        document_id=payload.document_id,
        revision_number=document.version,
        change_reason=payload.change_reason,
        created_by=payload.created_by,
        original_creation_date=document.created_at,
        observations=payload.observations,
        snapshot_data=snapshot,
        is_initial_revision=False,
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version


async def list_document_versions(
    db: AsyncSession,
    document_type: str,
    document_id: int,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[DocumentVersion]:
    """Retrieve all versions for a specific document."""
    result = await db.execute(
        select(DocumentVersion)
        .where(
            DocumentVersion.document_type == document_type,
            DocumentVersion.document_id == document_id,
        )
        .order_by(DocumentVersion.revision_number.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_document_version(
    db: AsyncSession,
    version_id: int,
) -> DocumentVersion:
    """Retrieve a specific document version by ID."""
    result = await db.execute(
        select(DocumentVersion).where(DocumentVersion.id == version_id)
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document version con id {version_id} no encontrada.",
        )
    return version
