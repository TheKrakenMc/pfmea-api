from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.pfmea_header import PfmeaHeader
    from app.models.user import User


class PfmeaTeamMember(Base):
    """Association between a PFMEA document and its core team members.

    Each member has a role within the team that governs their access level
    (PFMEA Owner, Team Member, Viewer) independently of their system-wide role.
    """

    __tablename__ = "pfmea_team_members"
    __table_args__ = (
        UniqueConstraint("pfmea_id", "user_id", name="uq_pfmea_team_pfmea_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pfmea_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pfmea_headers.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    role_in_team: Mapped[str] = mapped_column(
        String,
        default="Team Member",
        server_default="Team Member",
        comment="PFMEA Owner, Team Member, Viewer",
    )
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.now())
    department: Mapped[Optional[str]] = mapped_column(String, comment="Department of the member in the team")

    # Relationships
    pfmea: Mapped[Optional["PfmeaHeader"]] = relationship(
        back_populates="team_members"
    )
    user: Mapped[Optional["User"]] = relationship()

    @property
    def user_full_name(self) -> Optional[str]:
        return self.user.full_name if self.user else None

    @property
    def is_active(self) -> bool:
        if not self.user:
            return False
        return self.user.is_active and getattr(self.user, "deleted_at", None) is None
