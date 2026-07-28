from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, ForeignKey, String, Float, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.flowchart import Flowchart
    from app.models.plant import Plant
    from app.models.customer import Customer
    from app.models.technology import Technology
    from app.models.product_parameter import ProductParameter


class Product(Base, SoftDeleteMixin):
    """Manufactured product. Belongs to a plant, optionally linked to a customer."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("plants.id")
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("customers.id")
    )
    product_family_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("product_families.id")
    )
    production_line_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("production_lines.id")
    )
    part_number: Mapped[Optional[str]] = mapped_column(String)
    customer_part_number: Mapped[Optional[str]] = mapped_column(String)
    # Legacy property kept for backward compat — maps to customer_name in schemas
    @property
    def customer_name(self) -> Optional[str]:
        if self.customer:
            return self.customer.company_name
        return None
    description: Mapped[Optional[str]] = mapped_column(String)
    engineering_level: Mapped[Optional[str]] = mapped_column(String)
    drawing: Mapped[Optional[str]] = mapped_column(String)
    stage: Mapped[Optional[str]] = mapped_column(String)
    dimensions: Mapped[Optional[str]] = mapped_column(String)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    cycle_time: Mapped[Optional[float]] = mapped_column(Float)
    rate_per_hour: Mapped[Optional[float]] = mapped_column(Float)
    image_url: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String, default="Draft")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    plant: Mapped[Optional["Plant"]] = relationship(back_populates="products")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="products")
    flowcharts: Mapped[List["Flowchart"]] = relationship(back_populates="product")
    technologies: Mapped[List["Technology"]] = relationship(
        secondary="product_technology_mappings",
        viewonly=True
    )
    parameters: Mapped[List["ProductParameter"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
