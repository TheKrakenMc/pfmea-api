from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.technology import Technology
    from app.models.measurement_unit import MeasurementUnit


class TechnologyParameter(Base):
    """Critical process parameter tied to a specific technology/operation.

    Examples: Temperature (°C), Pressure (Bar), Torque (Nm).
    Each row captures the parameter metadata and optional target/limit values.
    """

    __tablename__ = "technology_parameters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    technology_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("technologies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Parameter name, e.g. Temperatura"
    )
    measurement_unit_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("measurement_units.id", ondelete="SET NULL"), nullable=True
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
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        onupdate=func.now(), nullable=True
    )

    # Relationships
    technology: Mapped[Optional["Technology"]] = relationship(
        back_populates="parameters"
    )
    measurement_unit: Mapped[Optional["MeasurementUnit"]] = relationship(
        lazy="selectin",
    )
