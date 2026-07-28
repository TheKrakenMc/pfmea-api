from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base, SoftDeleteMixin):
    """System role: Administrator, PFMEA Owner, Team Member, Viewer, Process Engineer."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    # Relationships
    users: Mapped[List["User"]] = relationship(
        back_populates="role",
        foreign_keys="[User.role_id]"
    )
