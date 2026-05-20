from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart import Flowchart
    from app.models.plant import Plant


class Product(Base):
    """A product manufactured at a plant (e.g., a specific part for a customer)."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("plant_id", "part_number", name="uq_products_plant_part"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plants.id"))
    customer_name: Mapped[Optional[str]] = mapped_column(
        String, comment="e.g., Ford, Tesla, VW"
    )
    part_number: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    plant: Mapped[Optional["Plant"]] = relationship(back_populates="products")
    flowcharts: Mapped[List["Flowchart"]] = relationship(back_populates="product")
