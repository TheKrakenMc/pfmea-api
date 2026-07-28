"""ControlPlan model — quality control document derived from PFMEA analysis."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.control_plan_item import ControlPlanItem
    from app.models.user import User


class ControlPlan(Base, SoftDeleteMixin):
    """A Control Plan document linked to a PFMEA project and flowchart."""

    __tablename__ = "control_plans"
    __table_args__ = (
        Index("ix_control_plans_pfmea_project_id", "pfmea_project_id"),
        Index("ix_control_plans_status", "status"),
        Index("ix_control_plans_owner_id", "owner_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pfmea_project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pfmea_headers.id"), nullable=False
    )
    flowchart_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("flowcharts.id"), nullable=False
    )
    control_plan_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[Optional[str]] = mapped_column(
        String, default="Draft", server_default="'Draft'"
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_revision_date: Mapped[Optional[date]] = mapped_column(Date)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    observations: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Relationships
    owner: Mapped[Optional["User"]] = relationship(foreign_keys=[owner_id])
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])
    items: Mapped[List["ControlPlanItem"]] = relationship(
        back_populates="control_plan",
        cascade="all, delete-orphan",
        order_by="ControlPlanItem.item_sequence",
    )
