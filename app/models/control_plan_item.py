"""ControlPlanItem model — individual line item within a Control Plan."""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


if TYPE_CHECKING:
    from app.models.control_plan import ControlPlan
    from app.models.control_plan_reaction import ControlPlanReaction
    from app.models.control_point_characteristic import ControlPointCharacteristic


class ControlPlanItem(Base):
    """A single item in a Control Plan, possibly linked to a failure mode or parameter control."""

    __tablename__ = "control_plan_items"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    control_plan_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("control_plans.id"), nullable=False
    )
    process_failure_mode_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("process_failure_modes.id")
    )
    process_parameter_control_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("process_parameter_controls.id")
    )
    item_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String, nullable=False)

    pfmea_worksheet_row_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pfmea_worksheet_rows.id", ondelete="SET NULL")
    )
    source_row_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    source_reviewed: Mapped[bool] = mapped_column(default=False, server_default="false")
    source_review_reason: Mapped[Optional[str]] = mapped_column(String)
    needs_review: Mapped[bool] = mapped_column(default=False, server_default="false")
    characteristic: Mapped[Optional[str]] = mapped_column(String)
    classification: Mapped[Optional[str]] = mapped_column(String(2))
    specification: Mapped[Optional[str]] = mapped_column(String)
    unit_id: Mapped[Optional[int]] = mapped_column(ForeignKey("measurement_units.id"))
    measurement_method: Mapped[Optional[str]] = mapped_column(String)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer)
    sample_frequency: Mapped[Optional[str]] = mapped_column(String)
    responsible_person_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    reaction_plan: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    control_plan: Mapped[Optional["ControlPlan"]] = relationship(back_populates="items")
    characteristics: Mapped[List["ControlPointCharacteristic"]] = relationship(
        back_populates="control_plan_item",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[List["ControlPlanReaction"]] = relationship(
        back_populates="control_plan_item",
        cascade="all, delete-orphan",
    )
