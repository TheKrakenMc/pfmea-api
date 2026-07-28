from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

class InstructionBase(BaseModel):
    title: str = Field(..., description="Instruction Sheet Title")
    status: str = Field("Draft")

class InstructionCreate(InstructionBase):
    pass

class InstructionRead(InstructionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
