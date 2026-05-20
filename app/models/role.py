from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    """Roles: Administrator, PFMEA Owner, Team Member, Viewer."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="role")
