from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


# ── Technology Schemas ──────────────────────────────────────────────────────
from app.schemas.technology_parameter import TechnologyParameterRead

class TechnologyBase(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    suggested_parameters: Optional[Dict[str, Any]] = None


class TechnologyCreate(TechnologyBase):
    plant_ids: Optional[List[int]] = None
    is_active: bool = True


class TechnologyUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    suggested_parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    plant_ids: Optional[List[int]] = None


class TechnologyRead(TechnologyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    parameters: List[TechnologyParameterRead] = []
