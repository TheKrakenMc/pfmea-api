from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

class Machinery(Base, SoftDeleteMixin):
    """Machinery and tools used in operations."""

    __tablename__ = "machinery"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    machinery_name: Mapped[str] = mapped_column(String)
    machinery_code: Mapped[str] = mapped_column(String)
    plant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("plants.id"))
    location_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("manufacturing_locations.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
