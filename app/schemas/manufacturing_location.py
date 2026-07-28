from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ManufacturingLocationBase(BaseModel):
    location_code: str = Field(..., max_length=255)
    location_name: str = Field(..., max_length=255)
    location_type: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    plant_id: int

class ManufacturingLocationCreate(ManufacturingLocationBase):
    pass

class ManufacturingLocationUpdate(BaseModel):
    location_code: Optional[str] = Field(None, max_length=255)
    location_name: Optional[str] = Field(None, max_length=255)
    location_type: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    plant_id: Optional[int] = None
    is_active: Optional[bool] = None

class ManufacturingLocationRead(ManufacturingLocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
