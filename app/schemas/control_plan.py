from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

class ControlPlanBase(BaseModel):
    title: str = Field(..., description="Control Plan Title")
    status: str = Field("Draft")

class ControlPlanCreate(ControlPlanBase):
    pass

class ControlPlanRead(ControlPlanBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
