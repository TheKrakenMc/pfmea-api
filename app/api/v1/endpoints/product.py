from typing import List, Optional

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
        db, skip=skip, limit=limit, q=q, status_filter=status_filter, customer_id=customer_id
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
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await product_service.create_product(db, payload)

@router.put("/{product_id}", response_model=ProductDetailRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await product_service.update_product(db, product_id, payload)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['Administrator'])),
):
    await product_service.delete_product(db, product_id)


# ── Product Versioning & History ───────────────────────────────────────────────

@router.put("/{product_id}/status", response_model=ProductDetailRead)
async def update_product_status(
    product_id: int,
    payload: ProductStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator'])),
):
    return await product_service.update_product_status(db, product_id, payload.status)

@router.post("/{product_id}/revisions", response_model=DocumentVersionRead, status_code=status.HTTP_201_CREATED)
async def create_product_revision(
    product_id: int,
    payload: ProductRevisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await product_service.create_product_revision(
        db, product_id, current_user.id, payload.change_reason, payload.engineering_level
    )

@router.get("/{product_id}/history", response_model=List[DocumentVersionRead])
async def get_product_history(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await product_service.get_product_history(db, product_id)

import os
import shutil
from fastapi import UploadFile, File

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member']))
):
    upload_dir = "uploads/products"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "path": file_path}

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
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Process Engineer'])),
):
    """Add a new parameter to a product."""
    return await product_service.create_parameter(db, product_id, payload)


@router.put("/parameters/{param_id}", response_model=ProductParameterRead)
async def update_parameter(
    param_id: int,
    payload: ProductParameterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Process Engineer'])),
):
    """Update an existing parameter."""
    return await product_service.update_parameter(db, param_id, payload)


@router.delete("/parameters/{param_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parameter(
    param_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Process Engineer'])),
):
    """Soft delete a parameter."""
    await product_service.delete_parameter(db, param_id)
