from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.control_plan_item import ControlPlanItem

class ControlPlanReaction(Base, SoftDeleteMixin):
    __tablename__ = "control_plan_reactions"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    control_plan_item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("control_plan_items.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    control_plan_item: Mapped[Optional["ControlPlanItem"]] = relationship(
        back_populates="reactions"
    )
