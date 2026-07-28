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

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
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

    # Relationships
    control_plan: Mapped[Optional["ControlPlan"]] = relationship(
        back_populates="items"
    )
    characteristics: Mapped[List["ControlPointCharacteristic"]] = relationship(
        back_populates="control_plan_item",
        cascade="all, delete-orphan",
    )
    reactions: Mapped[List["ControlPlanReaction"]] = relationship(
        back_populates="control_plan_item",
        cascade="all, delete-orphan",
    )
