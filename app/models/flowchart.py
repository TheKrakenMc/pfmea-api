from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart_step import FlowchartStep
    from app.models.pfmea_header import PfmeaHeader
    from app.models.product import Product
    from app.models.user import User


class Flowchart(Base):
    """Process-flow diagram for a product. Contains ordered steps."""

    __tablename__ = "flowcharts"
    __table_args__ = (Index("ix_flowcharts_product_id", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    title: Mapped[Optional[str]] = mapped_column(String)
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    status: Mapped[Optional[str]] = mapped_column(
        String, comment="Draft, Approved, Archived"
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    product: Mapped[Optional["Product"]] = relationship(back_populates="flowcharts")
    owner: Mapped[Optional["User"]] = relationship()
    steps: Mapped[List["FlowchartStep"]] = relationship(
        back_populates="flowchart",
        order_by="FlowchartStep.step_number",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pfmea_headers: Mapped[List["PfmeaHeader"]] = relationship(
        back_populates="flowchart"
    )
