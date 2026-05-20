from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart import Flowchart
    from app.models.pfmea_team_member import PfmeaTeamMember
    from app.models.process_item import ProcessItem
    from app.models.user import User


class PfmeaHeader(Base):
    """PFMEA document header — ties a FMEA analysis to an approved process flow."""

    __tablename__ = "pfmea_headers"
    __table_args__ = (Index("ix_pfmea_headers_flowchart_id", "flowchart_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    flowchart_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flowcharts.id"),
        comment="Ties the FMEA to the approved process flow",
    )
    pfmea_id_number: Mapped[Optional[str]] = mapped_column(
        String, unique=True, comment="e.g. OREGON_PFMEA_059_2026_1"
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    revision_date: Mapped[Optional[date]] = mapped_column(Date)
    confidentiality_level: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(
        String, comment="Draft, Submitted for Review, Approved, Archived"
    )
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    flowchart: Mapped[Optional["Flowchart"]] = relationship(
        back_populates="pfmea_headers"
    )
    owner: Mapped[Optional["User"]] = relationship()
    team_members: Mapped[List["PfmeaTeamMember"]] = relationship(
        back_populates="pfmea", cascade="all, delete-orphan"
    )
    process_items: Mapped[List["ProcessItem"]] = relationship(
        back_populates="pfmea", cascade="all, delete-orphan"
    )
