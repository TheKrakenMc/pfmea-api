from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.document_version import (
    DocumentVersionCreate,
    DocumentVersionRead,
)
from app.services import document_version_service

router = APIRouter(prefix="/document-versions", tags=["Document Versions"])


@router.post(
    "/",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document version",
)
async def create_document_version(
    payload: DocumentVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> DocumentVersionRead:
    version = await document_version_service.create_document_version(db, payload)
    return DocumentVersionRead.model_validate(version)


@router.get(
    "/{document_type}/{document_id}",
    response_model=List[DocumentVersionRead],
    summary="List versions for a specific document",
)
async def list_document_versions(
    document_type: str,
    document_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[DocumentVersionRead]:
    versions = await document_version_service.list_document_versions(
        db, document_type, document_id, skip=skip, limit=limit
    )
    return [DocumentVersionRead.model_validate(v) for v in versions]


@router.get(
    "/{version_id}",
    response_model=DocumentVersionRead,
    summary="Get a specific document version by ID",
)
async def get_document_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
) -> DocumentVersionRead:
    version = await document_version_service.get_document_version(db, version_id)
    return DocumentVersionRead.model_validate(version)
