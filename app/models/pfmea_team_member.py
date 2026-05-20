from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.pfmea_header import PfmeaHeader
    from app.models.user import User


class PfmeaTeamMember(Base):
    """Association between a PFMEA document and its team members."""

    __tablename__ = "pfmea_team_members"
    __table_args__ = (
        UniqueConstraint("pfmea_id", "user_id", name="uq_pfmea_team_pfmea_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pfmea_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pfmea_headers.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    pfmea: Mapped[Optional["PfmeaHeader"]] = relationship(
        back_populates="team_members"
    )
    user: Mapped[Optional["User"]] = relationship()
