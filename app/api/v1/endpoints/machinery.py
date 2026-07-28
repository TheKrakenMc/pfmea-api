from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.machinery import MachineryCreate, MachineryUpdate, MachineryRead
from app.services.machinery_service import machinery_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[MachineryRead])
async def read_machinery(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    plant_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    return await machinery_service.get_multi(db, skip=skip, limit=limit, q=q, plant_id=plant_id, is_active=is_active)

@router.post("/", response_model=MachineryRead)
async def create_machinery(
    *,
    db: AsyncSession = Depends(get_db),
    item_in: MachineryCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    return await machinery_service.create(db, obj_in=item_in)

@router.put("/{id}", response_model=MachineryRead)
async def update_machinery(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    item_in: MachineryUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    machinery = await machinery_service.get(db, id=id)
    if not machinery:
        raise HTTPException(status_code=404, detail="Machinery not found")
    return await machinery_service.update(db, db_obj=machinery, obj_in=item_in)

@router.get("/{id}", response_model=MachineryRead)
async def read_machinery_by_id(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    machinery = await machinery_service.get(db, id=id)
    if not machinery:
        raise HTTPException(status_code=404, detail="Machinery not found")
    return machinery

@router.delete("/{id}")
async def delete_machinery(
    *,
    db: AsyncSession = Depends(get_db),
    id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    machinery = await machinery_service.get(db, id=id)
    if not machinery:
        raise HTTPException(status_code=404, detail="Machinery not found")
    await machinery_service.remove(db, id=id)
    return {"ok": True}
