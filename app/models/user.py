from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.plant import Plant
    from app.models.role import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))
    plant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plants.id"), comment="Primary location of the user"
    )
    full_name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    role: Mapped[Optional["Role"]] = relationship(back_populates="users")
    plant: Mapped[Optional["Plant"]] = relationship(back_populates="users")
