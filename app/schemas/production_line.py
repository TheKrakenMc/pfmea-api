from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductionLineBase(BaseModel):
    name: str = Field(..., description="The name of the production line", max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the production line")
    is_active: bool = Field(default=True, description="Whether the production line is active and available for selection")


class ProductionLineCreate(ProductionLineBase):
    pass


class ProductionLineUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The name of the production line", max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the production line")
    is_active: Optional[bool] = Field(None, description="Whether the production line is active")


class ProductionLineRead(ProductionLineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductionLineListRead(ProductionLineBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
