from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.technology import Technology


class ProductTechnologyMapping(Base):
    """Many-to-many relationship between products and technologies."""

    __tablename__ = "product_technology_mappings"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "technology_id", name="uq_product_technology"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    technology_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    product: Mapped[Optional["Product"]] = relationship(viewonly=True)
    technology: Mapped[Optional["Technology"]] = relationship(viewonly=True)
