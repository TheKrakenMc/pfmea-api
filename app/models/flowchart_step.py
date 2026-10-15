from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


if TYPE_CHECKING:
    from app.models.flowchart import Flowchart
    from app.models.technology import Technology
    from app.models.machinery import Machinery


class FlowchartStep(Base):
    """A single step within a process flowchart."""

    __tablename__ = "flowchart_steps"
    __table_args__ = (
        UniqueConstraint(
            "flowchart_id",
            "step_number",
            "sub_step",
            name="uq_flowchart_steps_fc_step_sub",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    flowchart_id: Mapped[Optional[int]] = mapped_column(ForeignKey("flowcharts.id"))
    technology_id: Mapped[Optional[int]] = mapped_column(ForeignKey("technologies.id"))
    machinery_id: Mapped[Optional[int]] = mapped_column(ForeignKey("machinery.id"))
    step_number: Mapped[Optional[int]] = mapped_column(
        comment="e.g., 10, 20, 30. Used for ordering"
    )
    sub_step: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        comment="0 for master step, 1, 2... for intermediate sub-steps",
    )
    symbol_type: Mapped[str] = mapped_column(
        String, nullable=False, default="operation", server_default="operation"
    )
    responsible_department: Mapped[str] = mapped_column(
        String, nullable=False, default="Producción"
    )
    custom_description: Mapped[Optional[str]] = mapped_column(String)
    critical_flag: Mapped[str] = mapped_column(
        String, nullable=False, default="none", server_default="none"
    )
    product_characteristics: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    process_characteristics: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    target: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    flowchart: Mapped[Optional["Flowchart"]] = relationship(back_populates="steps")
    technology: Mapped[Optional["Technology"]] = relationship(
        back_populates="flowchart_steps"
    )
    machinery: Mapped[Optional["Machinery"]] = relationship()
