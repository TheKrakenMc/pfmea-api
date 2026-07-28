"""ManufacturingLocation model — physical work centres inside a plant."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin


class ManufacturingLocation(Base, SoftDeleteMixin):
    """A discrete manufacturing area within a plant (e.g. line, cell, station)."""

    __tablename__ = "manufacturing_locations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("plants.id"), nullable=False
    )
    location_code: Mapped[str] = mapped_column(String, nullable=False)
    location_name: Mapped[str] = mapped_column(String, nullable=False)
    location_type: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
