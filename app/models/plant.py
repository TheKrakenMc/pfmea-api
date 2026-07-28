from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.region import Region
    from app.models.technology import Technology
    from app.models.user import User


class Plant(Base, SoftDeleteMixin):
    """Manufacturing plant. Belongs to a region; has users, products, and technologies."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    region_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("regions.id")
    )
    name: Mapped[Optional[str]] = mapped_column(String)
    code: Mapped[Optional[str]] = mapped_column(String, unique=True)
    address: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    region: Mapped[Optional["Region"]] = relationship(back_populates="plants")
    users: Mapped[List["User"]] = relationship(
        back_populates="plant",
        foreign_keys="[User.plant_id]"
    )
    products: Mapped[List["Product"]] = relationship(back_populates="plant")
    technologies: Mapped[List["Technology"]] = relationship(
        secondary="plant_technologies",
        back_populates="plants"
    )
