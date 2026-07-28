from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductFamilyBase(BaseModel):
    name: str = Field(..., description="The name of the product family", max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the product family")
    is_active: bool = Field(default=True, description="Whether the product family is active and available for selection")


class ProductFamilyCreate(ProductFamilyBase):
    pass


class ProductFamilyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The name of the product family", max_length=255)
    description: Optional[str] = Field(None, description="Optional description of the product family")
    is_active: Optional[bool] = Field(None, description="Whether the product family is active")


class ProductFamilyRead(ProductFamilyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductFamilyListRead(ProductFamilyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
