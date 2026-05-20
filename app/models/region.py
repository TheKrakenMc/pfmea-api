from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.plant import Plant


class Region(Base):
    """Geographic regions: NAFTA, EMEA, APAC, etc."""

    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    # Relationships
    plants: Mapped[List["Plant"]] = relationship(back_populates="region")
