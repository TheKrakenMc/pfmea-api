from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.measurement_unit import MeasurementUnit
    from app.models.technology import Technology


class ProductParameter(Base):
    """Critical process parameter tied to a specific product.

    Examples: Temperature (°C), Pressure (Bar), Torque (Nm).
    Each row captures the parameter metadata and optional target/limit values.
    """

    __tablename__ = "product_parameters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Parameter name, e.g. Temperatura"
    )
    measurement_unit_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("measurement_units.id", ondelete="SET NULL"), nullable=True
    )
    technology_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("technologies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_value: Mapped[Optional[float]] = mapped_column(
        Float, comment="Nominal / target value"
    )
    min_value: Mapped[Optional[float]] = mapped_column(
        Float, comment="Lower specification limit"
    )
    max_value: Mapped[Optional[float]] = mapped_column(
        Float, comment="Upper specification limit"
    )
    is_critical: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", comment="CC / SC flag"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    order_index: Mapped[int] = mapped_column(
        nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        onupdate=func.now(), nullable=True
    )

    # Relationships
    product: Mapped[Optional["Product"]] = relationship(
        back_populates="parameters"
    )
    measurement_unit: Mapped[Optional["MeasurementUnit"]] = relationship(
        back_populates="parameters",
        lazy="selectin",
    )
    technology: Mapped[Optional["Technology"]] = relationship(
        lazy="selectin",
    )
