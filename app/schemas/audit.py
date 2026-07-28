from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field

class AuditBase(BaseModel):
    action: str = Field(..., description="Action performed")
    details: Optional[Any] = Field(None)

class AuditCreate(AuditBase):
    pass

class AuditRead(AuditBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
