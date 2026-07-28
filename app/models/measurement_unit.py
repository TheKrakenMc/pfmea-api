from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product_parameter import ProductParameter


class MeasurementUnit(Base):
    """Catalog of measurement units (e.g. m, kg, °C)."""

    __tablename__ = "measurement_units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    symbology: Mapped[str] = mapped_column(String(50), nullable=False)
    magnitude: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    parameters: Mapped[List["ProductParameter"]] = relationship(
        back_populates="measurement_unit"
    )
