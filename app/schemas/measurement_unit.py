from typing import Optional
from pydantic import BaseModel, Field

class MeasurementUnitBase(BaseModel):
    description: str = Field(..., max_length=255)
    symbology: str = Field(..., max_length=50)
    magnitude: str = Field(..., max_length=255)

class MeasurementUnitCreate(MeasurementUnitBase):
    pass

class MeasurementUnitUpdate(MeasurementUnitBase):
    description: Optional[str] = Field(None, max_length=255)
    symbology: Optional[str] = Field(None, max_length=50)
    magnitude: Optional[str] = Field(None, max_length=255)

class MeasurementUnit(MeasurementUnitBase):
    id: int

    class Config:
        from_attributes = True
