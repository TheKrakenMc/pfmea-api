from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.plant import Plant
    from app.models.role import Role
    from app.models.department import Department


class User(Base, SoftDeleteMixin):
    """Application user. Belongs to a plant and a role."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("roles.id")
    )
    plant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("plants.id"), comment="Primary location of the user"
    )
    full_name: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String)
    employment_position: Mapped[Optional[str]] = mapped_column(String)
    department_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("departments.id")
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    is_verified: Mapped[bool] = mapped_column(default=False, server_default="false")
    must_change_password: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    role: Mapped[Optional["Role"]] = relationship(
        back_populates="users",
        foreign_keys=[role_id]
    )
    plant: Mapped[Optional["Plant"]] = relationship(
        back_populates="users",
        foreign_keys=[plant_id]
     )
    department: Mapped[Optional["Department"]] = relationship(
        back_populates="users",
        foreign_keys=[department_id]
    )
