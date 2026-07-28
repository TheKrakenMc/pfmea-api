"""Pydantic v2 schemas for the PFMEA module (Header, Team, Worksheet Rows).

Covers AIAG-VDA 2019 Steps 1–6 with full CRUD schemas.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Team Members (Core Team)
# ---------------------------------------------------------------------------

class TeamMemberCreate(BaseModel):
    """Payload to add a team member to a PFMEA analysis."""
    user_id: int
    role_in_team: str = Field(
        "Team Member",
        description="Role within the PFMEA team",
    )
    department: str = Field(..., description="Department of the team member")


class TeamMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pfmea_id: Optional[int] = None
    user_id: Optional[int] = None
    role_in_team: str
    department: Optional[str] = None
    assigned_at: datetime
    user_full_name: Optional[str] = None
    is_active: bool = True

    @field_validator("user_full_name", mode="before")
    @classmethod
    def extract_user_name(cls, v, info):
        """Extract full_name from the User relationship if available."""
        if v is not None:
            return v
        # Access the raw ORM object via info.data
        return None


# ---------------------------------------------------------------------------
# Worksheet Rows (Steps 2–6)
# ---------------------------------------------------------------------------

class WorksheetRowBase(BaseModel):
    """Shared fields for worksheet row create/update."""
    flowchart_step_id: Optional[int] = None
    process_item_name: Optional[str] = None
    station_operation: Optional[str] = None
    work_element_process: Optional[str] = None
    operation_type: Optional[str] = None
    function_process_item_plant: Optional[str] = None
    function_process_item_customer: Optional[str] = None
    function_process_item_end_user: Optional[str] = None
    function_process_step: Optional[str] = None
    product_characteristic: Optional[str] = None
    function_work_element: Optional[str] = None
    process_characteristic: Optional[str] = None
    failure_mode: Optional[str] = None
    failure_effect_plant: Optional[str] = None
    failure_effect_customer: Optional[str] = None
    failure_effect_end_user: Optional[str] = None
    severity: Optional[int] = Field(None, ge=1, le=10)
    failure_cause: Optional[str] = None
    occurrence: Optional[int] = Field(None, ge=1, le=10)
    prevention_controls: Optional[str] = None
    detection_controls: Optional[str] = None
    detection: Optional[int] = Field(None, ge=1, le=10)
    optimization_prevention_action: Optional[str] = None
    optimization_detection_action: Optional[str] = None
    responsible_person_id: Optional[int] = None
    target_completion_date: Optional[date] = None
    action_status: Optional[str] = Field(
        None, pattern=r"^(Open|In Progress|Completed)$"
    )
    special_characteristics: Optional[str] = None
    actions_taken: Optional[str] = None
    completion_date: Optional[date] = None
    new_severity: Optional[int] = Field(None, ge=1, le=10)
    new_occurrence: Optional[int] = Field(None, ge=1, le=10)
    new_detection: Optional[int] = Field(None, ge=1, le=10)
    sequence_order: Optional[int] = None


class WorksheetRowCreate(WorksheetRowBase):
    """Payload for creating a new worksheet row."""
    pass


class WorksheetRowUpdate(WorksheetRowBase):
    """Payload for PATCH — all fields optional for partial updates."""
    id: Optional[int] = None


class WorksheetRowRead(WorksheetRowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pfmea_id: int
    action_priority: Optional[str] = None
    new_action_priority: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    responsible_person_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Action Priority Lookup
# ---------------------------------------------------------------------------

class ActionPriorityRequest(BaseModel):
    """Input for the AP lookup utility."""
    severity: int = Field(..., ge=1, le=10)
    occurrence: int = Field(..., ge=1, le=10)
    detection: int = Field(..., ge=1, le=10)


class ActionPriorityResult(BaseModel):
    """Result of the AIAG-VDA AP lookup."""
    severity: int
    occurrence: int
    detection: int
    action_priority: str = Field(..., pattern=r"^[HML]$")


# ---------------------------------------------------------------------------
# PFMEA Header (Step 1 — Global Header)
# ---------------------------------------------------------------------------

class PfmeaHeaderBase(BaseModel):
    """Shared fields for header create/update."""
    flowchart_id: Optional[int] = None
    project_name: Optional[str] = None
    customer: Optional[str] = None
    original_launch_date: Optional[date] = None
    part_number: Optional[str] = None
    product_description: Optional[str] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    confidentiality_level: Optional[str] = None


class PfmeaHeaderCreate(BaseModel):
    """Payload for creating a new PFMEA analysis."""
    flowchart_id: int
    project_name: str = Field(..., min_length=1, max_length=500)
    customer: str = Field(..., min_length=1, max_length=500)
    original_launch_date: Optional[date] = None
    part_number: Optional[str] = None
    product_description: Optional[str] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    confidentiality_level: Optional[str] = "Internal"
    team_members: List[TeamMemberCreate] = Field(default_factory=list)


class PfmeaHeaderUpdate(BaseModel):
    """Payload for PUT/PATCH on header fields (Step 1 metadata)."""
    project_name: Optional[str] = Field(None, min_length=1, max_length=500)
    customer: Optional[str] = Field(None, min_length=1, max_length=500)
    original_launch_date: Optional[date] = None
    part_number: Optional[str] = None
    product_description: Optional[str] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    confidentiality_level: Optional[str] = None
    revision_date: Optional[date] = None
    version: Optional[int] = None
    plant_id: Optional[int] = None
    pfmea_id_number: Optional[str] = None


class PfmeaHeaderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pfmea_id_number: Optional[str] = None
    flowchart_id: Optional[int] = None
    project_name: Optional[str] = None
    customer: Optional[str] = None
    original_launch_date: Optional[date] = None
    moc_status: str = "Draft"
    status: Optional[str] = None
    part_number: Optional[str] = None
    product_description: Optional[str] = None
    product_family_id: Optional[int] = None
    production_line_id: Optional[int] = None
    confidentiality_level: Optional[str] = None
    plant_id: Optional[int] = None
    owner_id: Optional[int] = None
    version: int = 1
    start_date: Optional[date] = None
    revision_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    team_members: List[TeamMemberRead] = []
    worksheet_row_count: Optional[int] = None
    high_priority_count: Optional[int] = None


class PfmeaHeaderDetailRead(PfmeaHeaderRead):
    """Extended read schema with worksheet rows included (for detail view)."""
    worksheet_rows: List[WorksheetRowRead] = []


# ---------------------------------------------------------------------------
# MOC Status Transition
# ---------------------------------------------------------------------------

class MocStatusTransition(BaseModel):
    """Payload for PATCH /pfmea-project/{id}/status"""
    new_status: str = Field(
        ...,
        pattern=r"^(Draft|In Review|Approved|Archived)$",
    )


# ---------------------------------------------------------------------------
# My Tasks (Pending Actions)
# ---------------------------------------------------------------------------

class PfmeaTaskRead(BaseModel):
    """A pending action item for the current user."""
    model_config = ConfigDict(from_attributes=True)

    row_id: int
    pfmea_id: int
    pfmea_id_number: Optional[str] = None
    project_name: Optional[str] = None
    failure_mode: Optional[str] = None
    action_priority: Optional[str] = None
    optimization_prevention_action: Optional[str] = None
    optimization_detection_action: Optional[str] = None
    target_completion_date: Optional[date] = None
    action_status: Optional[str] = None
