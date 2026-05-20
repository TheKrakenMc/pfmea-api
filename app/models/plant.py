from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.region import Region
    from app.models.technology import Technology
    from app.models.user import User


class Plant(Base):
    """Manufacturing plant. Belongs to a region; has users, products, and technologies."""

    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regions.id"))
    name: Mapped[Optional[str]] = mapped_column(String)
    code: Mapped[Optional[str]] = mapped_column(String, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Relationships
    region: Mapped[Optional["Region"]] = relationship(back_populates="plants")
    users: Mapped[List["User"]] = relationship(back_populates="plant")
    products: Mapped[List["Product"]] = relationship(back_populates="plant")
    technologies: Mapped[List["Technology"]] = relationship(back_populates="plant")
