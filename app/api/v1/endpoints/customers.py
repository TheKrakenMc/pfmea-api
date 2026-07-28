from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import customer_service
from app.api.deps import RoleChecker

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.get("/", response_model=List[CustomerRead])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    plant_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    return await customer_service.list_customers(
        db, skip=skip, limit=limit, q=q, status_filter=status_filter, plant_id=plant_id
    )

@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await customer_service.get_customer(db, customer_id)

@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await customer_service.create_customer(db, payload)

@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['PFMEA Owner', 'Administrator', 'Team Member'])),
):
    return await customer_service.update_customer(db, customer_id, payload)

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(RoleChecker(['Administrator'])),
):
    await customer_service.delete_customer(db, customer_id)
