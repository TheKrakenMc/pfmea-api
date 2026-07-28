from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, ForeignKey, String, Boolean, JSON, DateTime, UniqueConstraint, func, Table, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart_step import FlowchartStep
    from app.models.plant import Plant
    from app.models.user import User
    from app.models.technology_parameter import TechnologyParameter


plant_technologies = Table(
    "plant_technologies",
    Base.metadata,
    Column("plant_id", Integer, ForeignKey("plants.id", ondelete="CASCADE"), primary_key=True),
    Column("technology_id", Integer, ForeignKey("technologies.id", ondelete="CASCADE"), primary_key=True),
)

class Technology(Base):
    """Reusable operation types (e.g., AirLay, Assembly, PU Foaming)."""

    __tablename__ = "technologies"
    __table_args__ = (
        UniqueConstraint(
            "code", name="uq_technologies_code"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True, index=True, comment="Technology Code (e.g. ASM-01)")
    name: Mapped[str] = mapped_column(String, nullable=False, comment="Technology Name")
    category: Mapped[Optional[str]] = mapped_column(String, comment="Type/Category")
    description: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    suggested_parameters: Mapped[Optional[dict]] = mapped_column(JSON)
    
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    updated_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    plants: Mapped[List["Plant"]] = relationship(
        secondary=plant_technologies,
        back_populates="technologies"
    )
    flowchart_steps: Mapped[List["FlowchartStep"]] = relationship(
        back_populates="technology"
    )

    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship(foreign_keys=[updated_by])
    parameters: Mapped[List["TechnologyParameter"]] = relationship(
        back_populates="technology", cascade="all, delete-orphan"
    )

