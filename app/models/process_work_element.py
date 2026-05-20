from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.process_step import ProcessStep


class ProcessWorkElement(Base):
    """4M work-element classification: Machine, Man, Material (Indirect), Environment."""

    __tablename__ = "process_work_elements"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_step_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("process_steps.id")
    )
    element_type: Mapped[Optional[str]] = mapped_column(
        String, comment="Machine, Man, Material (Indirect), Environment"
    )
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    process_step: Mapped[Optional["ProcessStep"]] = relationship(
        back_populates="work_elements"
    )
