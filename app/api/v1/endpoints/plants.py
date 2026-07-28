from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.db import get_db
from app.models.plant import Plant
from app.schemas.plant import PlantRead
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[PlantRead], summary="List active plants")
async def list_plants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Plant).where(Plant.is_active == True)
    res = await db.execute(stmt)
    return res.scalars().all()
