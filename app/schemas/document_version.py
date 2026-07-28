from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentVersionBase(BaseModel):
    document_type: str = Field(..., description="Type of the document (e.g., 'flowchart', 'control_plan')")
    document_id: int = Field(..., description="ID of the original document")
    revision_number: int = Field(..., description="Revision number")
    change_reason: str = Field(..., description="Reason for the change")
    observations: Optional[str] = Field(None, description="Additional observations")
    snapshot_data: Optional[Dict[str, Any]] = Field(None, description="Snapshot of the document data")
    is_initial_revision: bool = Field(False, description="Whether this is the first revision")


class DocumentVersionCreate(DocumentVersionBase):
    created_by: int = Field(..., description="ID of the user who created this version")
    original_creation_date: datetime = Field(..., description="Original creation date of the document")


class DocumentVersionRead(DocumentVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: int
    created_at: datetime
    original_creation_date: datetime
