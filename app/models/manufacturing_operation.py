"""ManufacturingOperation model — reusable operation catalogue per plant."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin


class ManufacturingOperation(Base, SoftDeleteMixin):
    """A standard manufacturing operation within a plant (e.g. welding, painting)."""

    __tablename__ = "manufacturing_operations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("plants.id"), nullable=False
    )
    operation_name: Mapped[str] = mapped_column(String, nullable=False)
    operation_code: Mapped[Optional[str]] = mapped_column(String, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    operation_type: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
