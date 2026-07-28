from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.product_family import ProductFamilyCreate, ProductFamilyRead, ProductFamilyListRead, ProductFamilyUpdate
from app.services import product_family_service
from app.api.deps import RoleChecker

router = APIRouter(prefix="/product-families", tags=["Product Families"])


@router.get("/", response_model=List[ProductFamilyListRead])
async def list_product_families(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await product_family_service.list_product_families(
        db, skip=skip, limit=limit, active_only=active_only
    )


@router.get("/{family_id}", response_model=ProductFamilyRead)
async def get_product_family(
    family_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await product_family_service.get_product_family(db, family_id)


@router.post("/", response_model=ProductFamilyRead, status_code=status.HTTP_201_CREATED)
async def create_product_family(
    payload: ProductFamilyCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await product_family_service.create_product_family(db, payload)


@router.put("/{family_id}", response_model=ProductFamilyRead)
async def update_product_family(
    family_id: int,
    payload: ProductFamilyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await product_family_service.update_product_family(db, family_id, payload)


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_family(
    family_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator'])),
):
    await product_family_service.delete_product_family(db, family_id)
