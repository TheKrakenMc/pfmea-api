from pydantic import BaseModel
from typing import Optional

class PlantBase(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: bool = True

class PlantRead(PlantBase):
    id: int

    class Config:
        from_attributes = True
