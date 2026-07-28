from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.measurement_unit import MeasurementUnit
class TechnologyParameterBase(BaseModel):
    name: str = Field(..., max_length=255)
    measurement_unit_id: Optional[int] = None
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_critical: bool = False
    is_active: bool = True


class TechnologyParameterCreate(TechnologyParameterBase):
    pass


class TechnologyParameterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    measurement_unit_id: Optional[int] = None
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_critical: Optional[bool] = None
    is_active: Optional[bool] = None


class TechnologyParameterRead(TechnologyParameterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    technology_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    measurement_unit: Optional[MeasurementUnit] = None
