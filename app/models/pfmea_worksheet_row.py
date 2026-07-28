"""PfmeaWorksheetRow model — flat table for AIAG-VDA Steps 2–6."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart_step import FlowchartStep
    from app.models.pfmea_header import PfmeaHeader
    from app.models.user import User


class PfmeaWorksheetRow(Base):
    """Single row in the PFMEA worksheet covering Steps 2–6 (AIAG-VDA 2019).

    Each row links to a ``PfmeaHeader`` and optionally to a ``FlowchartStep``
    for downstream synchronisation of structure-analysis data.
    """

    __tablename__ = "pfmea_worksheet_rows"
    __table_args__ = (
        Index("ix_worksheet_rows_pfmea_id", "pfmea_id"),
        Index("ix_worksheet_rows_flowchart_step", "flowchart_step_id"),
        Index("ix_worksheet_rows_action_priority", "action_priority"),
        Index("ix_worksheet_rows_responsible", "responsible_person_id"),
        Index("ix_worksheet_rows_action_status", "action_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    pfmea_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pfmea_headers.id", ondelete="CASCADE"), nullable=False
    )
    flowchart_step_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("flowchart_steps.id", ondelete="SET NULL")
    )

    # Step 2: Structure Analysis (inherited from flowchart)
    process_item_name: Mapped[Optional[str]] = mapped_column(
        Text, comment="Process / subsystem name from flowchart"
    )
    station_operation: Mapped[Optional[str]] = mapped_column(
        Text, comment="Station / operation name"
    )
    work_element_process: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 2: Work Element Process (4M)"
    )
    operation_type: Mapped[Optional[str]] = mapped_column(
        Text, comment="Technology / operation type"
    )

    # Step 3: Function Analysis
    function_process_item_plant: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Process item function (Plant)"
    )
    function_process_item_customer: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Process item function (Customer)"
    )
    function_process_item_end_user: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Process item function (End User)"
    )
    function_process_step: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Process step function / requirement"
    )
    product_characteristic: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Product characteristics (Optional)"
    )
    function_work_element: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Work element function"
    )
    process_characteristic: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 3: Process characteristics (Optional)"
    )

    # Step 4: Failure Analysis
    failure_mode: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 4: Potential failure mode"
    )
    failure_effect_plant: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 4: Effect of failure (Plant)"
    )
    failure_effect_customer: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 4: Effect of failure (Customer)"
    )
    failure_effect_end_user: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 4: Effect of failure (End User)"
    )
    severity: Mapped[Optional[int]] = mapped_column(
        comment="Severity rating 1-10"
    )
    failure_cause: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 4: Potential cause of failure"
    )
    occurrence: Mapped[Optional[int]] = mapped_column(
        comment="Occurrence rating 1-10"
    )

    # Step 5: Risk Analysis (Current Controls)
    prevention_controls: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 5: Current prevention controls"
    )
    detection_controls: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 5: Current detection controls"
    )
    detection: Mapped[Optional[int]] = mapped_column(
        comment="Detection rating 1-10"
    )
    action_priority: Mapped[Optional[str]] = mapped_column(
        String, comment="Auto-calculated: H, M, L (AIAG-VDA AP)"
    )
    special_characteristics: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 5: Special Characteristics"
    )

    # Step 6: Optimization
    optimization_prevention_action: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 6: Recommended prevention action"
    )
    optimization_detection_action: Mapped[Optional[str]] = mapped_column(
        Text, comment="Step 6: Recommended detection action"
    )
    responsible_person_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date)
    action_status: Mapped[Optional[str]] = mapped_column(
        String, default="Open", server_default="Open",
        comment="Open, In Progress, Completed"
    )
    actions_taken: Mapped[Optional[str]] = mapped_column(Text)
    completion_date: Mapped[Optional[date]] = mapped_column(Date)

    # Re-evaluation (after optimisation)
    new_severity: Mapped[Optional[int]] = mapped_column(
        comment="Re-evaluated severity 1-10"
    )
    new_occurrence: Mapped[Optional[int]] = mapped_column(
        comment="Re-evaluated occurrence 1-10"
    )
    new_detection: Mapped[Optional[int]] = mapped_column(
        comment="Re-evaluated detection 1-10"
    )
    new_action_priority: Mapped[Optional[str]] = mapped_column(
        String, comment="Re-evaluated AP: H, M, L"
    )

    # Row ordering
    sequence_order: Mapped[int] = mapped_column(default=0, server_default="0")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    pfmea: Mapped[Optional["PfmeaHeader"]] = relationship(
        back_populates="worksheet_rows"
    )
    flowchart_step: Mapped[Optional["FlowchartStep"]] = relationship()
    responsible_person: Mapped[Optional["User"]] = relationship(
        foreign_keys=[responsible_person_id]
    )
