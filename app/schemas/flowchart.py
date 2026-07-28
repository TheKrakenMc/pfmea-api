"""Pydantic schemas for Flowchart and FlowchartStep (nested creation)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.technology import TechnologyRead
from app.schemas.machinery import MachineryRead
from app.schemas.product import ProductCustomerRead


# ---------------------------------------------------------------------------
# FlowchartStep
# ---------------------------------------------------------------------------

class FlowchartStepBase(BaseModel):
    technology_id: Optional[int] = None
    machinery_id: Optional[int] = None
    step_number: int = Field(..., gt=0, description="Must be positive (e.g., 10, 20, 30)")
    symbol_type: str = "operation"
    responsible_department: str = "Producción"
    custom_description: Optional[str] = None
    critical_flag: str = "none"


class FlowchartStepCreate(FlowchartStepBase):
    """Payload for creating a step inside a flowchart."""
    pass


class FlowchartStepRead(FlowchartStepBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    flowchart_id: int
    technology: Optional[TechnologyRead] = None
    machinery: Optional[MachineryRead] = None


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
    description: Optional[str] = None
    customer: Optional[ProductCustomerRead] = None


class ProductCreate(BaseModel):
    plant_id: Optional[int] = None
    customer_name: str = Field(..., min_length=1, max_length=255)
    part_number: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Flowchart
# ---------------------------------------------------------------------------

class FlowchartBase(BaseModel):
    product_id: int
    owner_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    confidentiality_level: Optional[str] = None
    status: Optional[str] = Field("Draft", pattern=r"^(Draft|In Review|Approved|Archived)$")


class FlowchartCreate(FlowchartBase):
    """Nested creation: send a flowchart with all its steps in one request."""

    steps: List[FlowchartStepCreate] = Field(
        default_factory=list,
        description="Ordered list of process-flow steps",
    )


class FlowchartUpdate(BaseModel):
    """Payload to update flowchart metadata and its associated product details."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    confidentiality_level: Optional[str] = None
    status: Optional[str] = Field(None, pattern=r"^(Draft|In Review|Approved|Archived)$")
    customer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    part_number: Optional[str] = Field(None, min_length=1, max_length=255)
    product_description: Optional[str] = None


class FlowchartRead(FlowchartBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    flowchart_code: Optional[str] = None
    version: int
    created_at: datetime
    updated_at: datetime
    steps: List[FlowchartStepRead] = []
    product: Optional[ProductRead] = None


# ---------------------------------------------------------------------------
# Bulk step reorder / replace
# ---------------------------------------------------------------------------

class FlowchartStepsReorder(BaseModel):
    """Payload for PUT /flowcharts/{id}/steps — replaces all steps atomically."""

    steps: List[FlowchartStepCreate] = Field(
        ...,
        description="Ordered list of steps that will replace the current ones",
    )


# ---------------------------------------------------------------------------
# Archive action
# ---------------------------------------------------------------------------

class FlowchartArchivePayload(BaseModel):
    """Payload for PATCH /flowcharts/{id}/archive."""

    change_reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Mandatory reason for archiving (min 10 characters)",
    )
    eco_number: Optional[str] = Field(
        None,
        max_length=100,
        description="Engineering Change Order number (optional)",
    )


# ---------------------------------------------------------------------------
# History / Audit Trail
# ---------------------------------------------------------------------------

class UserMinimalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    employment_position: Optional[str] = None


class DocumentVersionReadExtended(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_type: str
    document_id: int
    revision_number: int
    change_reason: str
    created_by: int
    created_at: datetime
    original_creation_date: datetime
    observations: Optional[str] = None
    snapshot_data: Optional[Dict[str, Any]] = None
    is_initial_revision: bool = False
    creator: Optional[UserMinimalRead] = None


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    performed_by: int
    action_details: Optional[str] = None
    previous_values: Optional[Any] = None
    new_values: Optional[Any] = None
    performed_at: datetime
    performer: Optional[UserMinimalRead] = None


class FlowchartHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    flowchart_id: int
    versions: List[DocumentVersionReadExtended] = []
    audit_logs: List[AuditLogRead] = []
