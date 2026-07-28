"""Customer model — external customer entity scoped to a plant."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.plant import Plant
    from app.models.product import Product


class Customer(Base, SoftDeleteMixin):
    """Customer record associated with a plant."""

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_customer_code", "customer_code"),
        Index("ix_customers_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    plant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("plants.id"), nullable=False
    )
    customer_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    tax_registry: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(String, default="active", server_default="'active'")
    address: Mapped[Optional[str]] = mapped_column(String)
    city: Mapped[Optional[str]] = mapped_column(String)
    state: Mapped[Optional[str]] = mapped_column(String)
    postal_code: Mapped[Optional[str]] = mapped_column(String)
    country: Mapped[Optional[str]] = mapped_column(String)
    contact_email: Mapped[Optional[str]] = mapped_column(String)
    logo_url: Mapped[Optional[str]] = mapped_column(String)
    brand_logo_url: Mapped[Optional[str]] = mapped_column(String)
    provider_code: Mapped[Optional[str]] = mapped_column(String)
    observations: Mapped[Optional[str]] = mapped_column(String)
    safety_characteristic: Mapped[Optional[str]] = mapped_column(String, default="D", server_default="'D'")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    plant: Mapped[Optional["Plant"]] = relationship()
    products: Mapped[List["Product"]] = relationship(back_populates="customer")
