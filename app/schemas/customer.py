from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CustomerBase(BaseModel):
    customer_code: str = Field(..., max_length=255)
    company_name: str = Field(..., max_length=255)
    tax_registry: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field("active", max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    brand_logo_url: Optional[str] = None
    provider_code: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = None
    safety_characteristic: Optional[str] = Field("D", max_length=50)

class CustomerCreate(CustomerBase):
    plant_id: int

class CustomerUpdate(BaseModel):
    customer_code: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    tax_registry: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    brand_logo_url: Optional[str] = None
    provider_code: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = None
    safety_characteristic: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class CustomerRead(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plant_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
