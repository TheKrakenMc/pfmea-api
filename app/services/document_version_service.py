"""Service layer for DocumentVersion business logic."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.document_version import DocumentVersion
from app.schemas.document_version import DocumentVersionCreate


async def create_document_version(
    db: AsyncSession,
    payload: DocumentVersionCreate,
) -> DocumentVersion:
    """Create a new document version record."""
    version = DocumentVersion(
        document_type=payload.document_type,
        document_id=payload.document_id,
        revision_number=payload.revision_number,
        change_reason=payload.change_reason,
        created_by=payload.created_by,
        original_creation_date=payload.original_creation_date,
        observations=payload.observations,
        snapshot_data=payload.snapshot_data,
        is_initial_revision=payload.is_initial_revision,
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
