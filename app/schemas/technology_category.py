from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TechnologyCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True


class TechnologyCategoryCreate(TechnologyCategoryBase):
    pass


class TechnologyCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TechnologyCategoryRead(TechnologyCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
