from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class ControlPlanItemBase(BaseModel):
    item_sequence: int
    item_name: str
    process_failure_mode_id: Optional[int] = None
    process_parameter_control_id: Optional[int] = None


class ControlPlanItemCreate(ControlPlanItemBase):
    pass


class ControlPlanItemUpdate(BaseModel):
    item_sequence: Optional[int] = None
    item_name: Optional[str] = None
    characteristic: Optional[str] = None
    classification: Optional[str] = Field(None, pattern=r"^(CC|SC)$")
    specification: Optional[str] = None
    unit_id: Optional[int] = Field(None, gt=0)
    measurement_method: Optional[str] = None
    sample_size: Optional[int] = Field(None, gt=0)
    sample_frequency: Optional[str] = None
    responsible_person_id: Optional[int] = Field(None, gt=0)
    reaction_plan: Optional[str] = None


class ControlPlanItemRead(ControlPlanItemBase, ControlPlanItemUpdate):
    pfmea_worksheet_row_id: Optional[int] = None
    source_row_id: Optional[int] = None
    is_active: bool = True
    source_reviewed: bool = False
    source_review_reason: Optional[str] = None
    needs_review: bool = False
    model_config = ConfigDict(from_attributes=True)
    id: int
    control_plan_id: int


class ControlPlanBase(BaseModel):
    title: str = Field(..., description="Control Plan Title")
    status: str = Field("Draft")
    observations: Optional[str] = None


class ControlPlanCreate(ControlPlanBase):
    pass


class ControlPlanUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    observations: Optional[str] = None
    is_active: Optional[bool] = None


class ControlPlanRead(ControlPlanBase):
    lock_version: int = 1
    needs_review: bool = False
    model_config = ConfigDict(from_attributes=True)
    id: int
    pfmea_project_id: int
    flowchart_id: int
    control_plan_code: str
    version: int
    start_date: date
    owner_id: int
    created_at: datetime
    updated_at: datetime
    items: List[ControlPlanItemRead] = []
