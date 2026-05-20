from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.process_item import ProcessItem
    from app.models.process_work_element import ProcessWorkElement


class ProcessStep(Base):
    """Focus Element within a Process Item (Step 2 detail)."""

    __tablename__ = "process_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("process_items.id")
    )
    station_number: Mapped[Optional[str]] = mapped_column(String)
    step_name: Mapped[Optional[str]] = mapped_column(
        String, comment="Name of Focus Element"
    )
    sequence_order: Mapped[Optional[int]] = mapped_column()

    # Relationships
    process_item: Mapped[Optional["ProcessItem"]] = relationship(
        back_populates="process_steps"
    )
    work_elements: Mapped[List["ProcessWorkElement"]] = relationship(
        back_populates="process_step", cascade="all, delete-orphan"
    )
