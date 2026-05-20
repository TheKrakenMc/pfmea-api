"""Pydantic schemas for Flowchart and FlowchartStep (nested creation)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# FlowchartStep
# ---------------------------------------------------------------------------

class FlowchartStepBase(BaseModel):
    technology_id: Optional[int] = None
    step_number: int = Field(..., gt=0, description="Must be positive (e.g., 10, 20, 30)")
    custom_description: Optional[str] = Field(None, max_length=500)


class FlowchartStepCreate(FlowchartStepBase):
    """Payload for creating a step inside a flowchart."""
    pass


class FlowchartStepRead(FlowchartStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    flowchart_id: int


# ---------------------------------------------------------------------------
# Flowchart
# ---------------------------------------------------------------------------

class FlowchartBase(BaseModel):
    product_id: int
    owner_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    status: Optional[str] = Field("Draft", pattern=r"^(Draft|Approved|Archived)$")


class FlowchartCreate(FlowchartBase):
    """Nested creation: send a flowchart with all its steps in one request."""

    steps: List[FlowchartStepCreate] = Field(
        default_factory=list,
        description="Ordered list of process-flow steps",
    )


class FlowchartRead(FlowchartBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    created_at: datetime
    updated_at: datetime
    steps: List[FlowchartStepRead] = []


# ---------------------------------------------------------------------------
# Bulk step reorder / replace
# ---------------------------------------------------------------------------

class FlowchartStepsReorder(BaseModel):
    """Payload for PUT /flowcharts/{id}/steps — replaces all steps atomically."""

    steps: List[FlowchartStepCreate] = Field(
        ...,
        description="Ordered list of steps that will replace the current ones",
    )
