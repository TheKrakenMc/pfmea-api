"""AuditLog model — records write operations on critical entities.

Extended with field-level granularity columns (entity_type, entity_id,
field_name, old_value, new_value) for PFMEA MOC audit trail.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """Row in ``document_audit_logs``. Created automatically by the audit middleware
    and programmatically by the PFMEA service for field-level tracking."""

    __tablename__ = "document_audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_performed_at", "performed_at"),
        Index("ix_audit_logs_performed_by", "performed_by"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    flowchart_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("flowcharts.id")
    )
    pfmea_project_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("pfmea_headers.id")
    )
    control_plan_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("control_plans.id")
    )
    operation_instruction_sheet_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("instruction_sheets.id")
    )

    action: Mapped[str] = mapped_column(String, nullable=False)
    performed_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    action_details: Mapped[Optional[str]] = mapped_column(String)
    previous_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Field-level audit granularity (added for PFMEA MOC tracking)
    entity_type: Mapped[Optional[str]] = mapped_column(
        Text, comment="e.g. pfmea_header, pfmea_worksheet_row, pfmea_team_member"
    )
    entity_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, comment="PK of the affected entity"
    )
    field_name: Mapped[Optional[str]] = mapped_column(
        Text, comment="Name of the modified column"
    )
    old_value: Mapped[Optional[str]] = mapped_column(
        Text, comment="Previous value (serialised to text)"
    )
    new_value: Mapped[Optional[str]] = mapped_column(
        Text, comment="New value (serialised to text)"
    )

    # Relationships
    performer: Mapped[Optional["User"]] = relationship(foreign_keys=[performed_by])
