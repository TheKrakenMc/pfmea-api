from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.pfmea_header import PfmeaHeader
    from app.models.process_step import ProcessStep


class ProcessItem(Base):
    """Step 2 — Structure Analysis: System, Subsystem, Part, or Process Name."""

    __tablename__ = "process_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    pfmea_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pfmea_headers.id"))
    item_name: Mapped[Optional[str]] = mapped_column(
        String, comment="System, Subsystem, Part, or Process Name"
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    sequence_order: Mapped[Optional[int]] = mapped_column()

    # Relationships
    pfmea: Mapped[Optional["PfmeaHeader"]] = relationship(
        back_populates="process_items"
    )
    process_steps: Mapped[List["ProcessStep"]] = relationship(
        back_populates="process_item",
        order_by="ProcessStep.sequence_order",
        cascade="all, delete-orphan",
    )
