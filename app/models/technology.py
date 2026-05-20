from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart_step import FlowchartStep
    from app.models.plant import Plant


class Technology(Base):
    """Reusable operation types per plant (e.g., AirLay, Assembly, PU Foaming)."""

    __tablename__ = "technologies"
    __table_args__ = (
        UniqueConstraint(
            "plant_id", "operation_name", name="uq_technologies_plant_op"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plants.id"))
    operation_name: Mapped[Optional[str]] = mapped_column(
        String, comment="e.g., AirLay, Assembly, PU Foaming"
    )

    # Relationships
    plant: Mapped[Optional["Plant"]] = relationship(back_populates="technologies")
    flowchart_steps: Mapped[List["FlowchartStep"]] = relationship(
        back_populates="technology"
    )
