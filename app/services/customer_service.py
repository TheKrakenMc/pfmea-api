from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

async def list_customers(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    status_filter: Optional[str] = None,
    plant_id: Optional[int] = None
) -> List[Customer]:
    stmt = select(Customer).where(Customer.is_active == True)

    if q:
        stmt = stmt.where(
            or_(
                Customer.customer_code.ilike(f"%{q}%"),
                Customer.company_name.ilike(f"%{q}%"),
                Customer.contact_email.ilike(f"%{q}%")
            )
        )
    
    if status_filter:
        stmt = stmt.where(Customer.status == status_filter)
        
    if plant_id:
        stmt = stmt.where(Customer.plant_id == plant_id)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_customer(db: AsyncSession, customer_id: int) -> Customer:
    stmt = select(Customer).where(Customer.id == customer_id, Customer.is_active == True)
    
    result = await db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer

async def create_customer(db: AsyncSession, payload: CustomerCreate) -> Customer:
    customer_dict = payload.model_dump()
    
    db_customer = Customer(**customer_dict)
    db.add(db_customer)
    await db.flush()
    await db.commit()
    await db.refresh(db_customer)
    
    return db_customer

async def update_customer(db: AsyncSession, customer_id: int, payload: CustomerUpdate) -> Customer:
    db_customer = await get_customer(db, customer_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
            
    await db.commit()
    await db.refresh(db_customer)
    return db_customer

async def delete_customer(db: AsyncSession, customer_id: int) -> None:
    db_customer = await get_customer(db, customer_id)
    db_customer.is_active = False
    await db.commit()
