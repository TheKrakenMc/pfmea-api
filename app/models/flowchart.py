from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.flowchart_step import FlowchartStep
    from app.models.pfmea_header import PfmeaHeader
    from app.models.product import Product
    from app.models.user import User


class Flowchart(Base, SoftDeleteMixin):
    """Process-flow diagram for a product. Contains ordered steps."""

    __tablename__ = "flowcharts"
    __table_args__ = (Index("ix_flowcharts_product_id", "product_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("plants.id")
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("products.id")
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    flowchart_code: Mapped[Optional[str]] = mapped_column(String, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String)
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    status: Mapped[Optional[str]] = mapped_column(
        String, comment="Draft, Approved, Archived"
    )
    production_stage: Mapped[Optional[str]] = mapped_column(String)
    manufacturing_location_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("manufacturing_locations.id")
    )
    description: Mapped[Optional[str]] = mapped_column(String)
    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    observations: Mapped[Optional[str]] = mapped_column(String)
    confidentiality_level: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Relationships
    product: Mapped[Optional["Product"]] = relationship(back_populates="flowcharts")
    owner: Mapped[Optional["User"]] = relationship(
        foreign_keys=[owner_id]
    )
    creator: Mapped[Optional["User"]] = relationship(
        foreign_keys=[created_by]
    )
    steps: Mapped[List["FlowchartStep"]] = relationship(
        back_populates="flowchart",
        order_by="FlowchartStep.step_number",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pfmea_headers: Mapped[List["PfmeaHeader"]] = relationship(
        back_populates="flowchart"
    )
