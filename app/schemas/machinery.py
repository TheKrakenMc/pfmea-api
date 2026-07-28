from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MachineryBase(BaseModel):
    machinery_name: str
    machinery_code: str
    plant_id: int
    location_id: Optional[int] = None
    is_active: bool = True

class MachineryCreate(MachineryBase):
    pass

class MachineryUpdate(BaseModel):
    machinery_name: Optional[str] = None
    machinery_code: Optional[str] = None
    plant_id: Optional[int] = None
    location_id: Optional[int] = None
    is_active: Optional[bool] = None

class MachineryRead(MachineryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
