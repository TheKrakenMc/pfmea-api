from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


from app.schemas.technology import TechnologyRead
from app.schemas.measurement_unit import MeasurementUnit

# ---------------------------------------------------------------------------
# Product Parameters
# ---------------------------------------------------------------------------

class ProductParameterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    measurement_unit_id: Optional[int] = None
    technology_id: Optional[int] = None
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_critical: bool = False
    order_index: int = 0


class ProductParameterCreate(ProductParameterBase):
    pass


class ProductParameterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    measurement_unit_id: Optional[int] = None
    technology_id: Optional[int] = None
    target_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_critical: Optional[bool] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


class ProductParameterRead(ProductParameterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    measurement_unit: Optional[MeasurementUnit] = None

# ---------------------------------------------------------------------------
# Product Customer
# ---------------------------------------------------------------------------

class ProductCustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    customer_code: str
    safety_characteristic: Optional[str] = None


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plant_id: Optional[int] = None
    customer_name: Optional[str] = None
    part_number: Optional[str] = None
    customer_part_number: Optional[str] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    description: Optional[str] = None
    engineering_level: Optional[str] = None
    drawing: Optional[str] = None
    stage: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    cycle_time: Optional[float] = None
    rate_per_hour: Optional[float] = None
    image_url: Optional[str] = None
    status: Optional[str] = "Draft"
    version: int = 1
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    customer: Optional[ProductCustomerRead] = None
    technologies: List[TechnologyRead] = []


class ProductRevisionCreate(BaseModel):
    change_reason: str = Field(..., min_length=1)
    engineering_level: str = Field(..., min_length=1)


class ProductStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(Draft|In Review|Released|Archived)$")


class ProductBase(BaseModel):
    part_number: str = Field(..., min_length=1, max_length=255)
    customer_part_number: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    engineering_level: Optional[str] = None
    drawing: Optional[str] = None
    stage: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    cycle_time: Optional[float] = None
    rate_per_hour: Optional[float] = None
    image_url: Optional[str] = None
    status: Optional[str] = Field("active", max_length=50)


class ProductCreate(ProductBase):
    plant_id: Optional[int] = None
    customer_id: Optional[int] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    technology_ids: List[int] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    part_number: Optional[str] = Field(None, min_length=1, max_length=255)
    customer_part_number: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    engineering_level: Optional[str] = None
    drawing: Optional[str] = None
    stage: Optional[str] = None
    dimensions: Optional[str] = None
    weight: Optional[float] = None
    cycle_time: Optional[float] = None
    rate_per_hour: Optional[float] = None
    image_url: Optional[str] = None
    customer_id: Optional[int] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    status: Optional[str] = Field(None, max_length=50)
    technology_ids: Optional[List[int]] = None


class ProductListRead(ProductRead):
    pass


class ProductDetailRead(ProductRead):
    parameters: List[ProductParameterRead] = []
