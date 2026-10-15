from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schemas.product import (
    ProductCreate,
    ProductDetailRead,
    ProductListRead,
    ProductUpdate,
    ProductParameterRead,
    ProductParameterCreate,
    ProductParameterUpdate,
    ProductRevisionCreate,
    ProductStatusUpdate,
)
from app.schemas.document_version import DocumentVersionRead
from app.services import product_service
from app.api.deps import RoleChecker
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductListRead])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await product_service.list_products(
        db,
        skip=skip,
        limit=limit,
        q=q,
        status_filter=status_filter,
        customer_id=customer_id,
    )


@router.get("/{product_id}", response_model=ProductDetailRead)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await product_service.get_product(db, product_id)


@router.post("/", response_model=ProductDetailRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker(["PFMEA Owner", "Administrator", "Team Member"])),
):
    return await product_service.create_product(db, payload)


@router.put("/{product_id}", response_model=ProductDetailRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker(["PFMEA Owner", "Administrator", "Team Member"])),
):
    return await product_service.update_product(db, product_id, payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker(["Administrator"])),
):
    await product_service.delete_product(db, product_id)


# ── Product Versioning & History ───────────────────────────────────────────────


@router.put("/{product_id}/status", response_model=ProductDetailRead)
async def update_product_status(
    product_id: int,
    payload: ProductStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker(["PFMEA Owner", "Administrator"])),
):
    return await product_service.update_product_status(db, product_id, payload.status)


@router.post(
    "/{product_id}/revisions",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product_revision(
    product_id: int,
    payload: ProductRevisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker(["PFMEA Owner", "Administrator"])),
):
    return await product_service.create_product_revision(
        db,
        product_id,
        current_user.id,
        payload.change_reason,
        payload.engineering_level,
    )


@router.get("/{product_id}/history", response_model=List[DocumentVersionRead])
async def get_product_history(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await product_service.get_product_history(db, product_id)


UPLOAD_ROOT = Path("uploads/products")
MAX_IMAGE_BYTES = 5 * 1024 * 1024


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user=Depends(RoleChecker(["PFMEA Owner", "Administrator", "Team Member"])),
):
    content = await file.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image exceeds 5 MB")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = "png"
    elif content.startswith(b"\xff\xd8\xff"):
        extension = "jpg"
    elif content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        extension = "webp"
    else:
        raise HTTPException(415, "Only PNG, JPEG and WebP images are accepted")
    filename = f"{uuid4().hex}.{extension}"
    directory = UPLOAD_ROOT / str(current_user.plant_id)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_bytes(content)
    return {
        "filename": filename,
        "path": f"/api/v1/products/images/{current_user.plant_id}/{filename}",
    }


@router.get("/images/{plant_id}/{filename}")
async def product_image(
    plant_id: int,
    filename: str,
    current_user=Depends(
        RoleChecker(
            [
                "PFMEA Owner",
                "Administrator",
                "Team Member",
                "Viewer",
                "Process Engineer",
            ]
        )
    ),
):
    import re

    if not re.fullmatch(r"[a-f0-9]{32}\.(png|jpg|webp)", filename):
        raise HTTPException(404, "Image not found")
    target = UPLOAD_ROOT / str(plant_id) / filename
    if not target.is_file():
        raise HTTPException(404, "Image not found")
    return FileResponse(
        target,
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ── Product Parameter Sub-resource ───────────────────────────────────────


@router.get("/{product_id}/parameters", response_model=List[ProductParameterRead])
async def list_parameters(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List active parameters for a product."""
    return await product_service.list_parameters(db, product_id)


@router.post(
    "/{product_id}/parameters",
    response_model=ProductParameterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_parameter(
    product_id: int,
    payload: ProductParameterCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        RoleChecker(["PFMEA Owner", "Administrator", "Process Engineer"])
    ),
):
    """Add a new parameter to a product."""
    return await product_service.create_parameter(db, product_id, payload)


@router.put("/parameters/{param_id}", response_model=ProductParameterRead)
async def update_parameter(
    param_id: int,
    payload: ProductParameterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        RoleChecker(["PFMEA Owner", "Administrator", "Process Engineer"])
    ),
):
    """Update an existing parameter."""
    return await product_service.update_parameter(db, param_id, payload)


@router.delete("/parameters/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter(
    param_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        RoleChecker(["PFMEA Owner", "Administrator", "Process Engineer"])
    ),
):
    """Soft delete a parameter."""
    await product_service.delete_parameter(db, param_id)


class ParameterChange(ProductParameterCreate):
    id: int | None = None


class ParameterBulkSave(BaseModel):
    expected_version: int = Field(ge=1)
    rows: list[ParameterChange] = Field(default_factory=list)
    deleted_row_ids: list[int] = Field(default_factory=list)


@router.put("/{product_id}/parameters/bulk", response_model=ProductDetailRead)
async def save_parameters(
    product_id: int,
    payload: ParameterBulkSave,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker(["PFMEA Owner", "Administrator", "Team Member"])),
):
    from app.models import ProductParameter
    from sqlalchemy import select

    rows = {
        row.id: row
        for row in (
            await db.scalars(
                select(ProductParameter).where(
                    ProductParameter.product_id == product_id
                )
            )
        ).all()
    }
    removed = set(payload.deleted_row_ids)
    changed = [row.id for row in payload.rows if row.id is not None]
    if len(changed) != len(set(changed)) or removed.intersection(changed):
        raise HTTPException(400, "Repeated parameter or conflicting deletion")
    if any(row_id not in rows for row_id in [*removed, *changed]):
        raise HTTPException(400, "Parameter does not belong to product")
    for row_id in removed:
        rows[row_id].is_active = False
    for update in payload.rows:
        values = update.model_dump(exclude={"id"})
        if update.id is None:
            db.add(ProductParameter(product_id=product_id, **values))
        else:
            for key, value in values.items():
                setattr(rows[update.id], key, value)
    await db.flush()
    return await product_service.get_product(db, product_id)
