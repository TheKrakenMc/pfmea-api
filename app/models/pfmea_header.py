from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.flowchart import Flowchart
    from app.models.pfmea_team_member import PfmeaTeamMember
    from app.models.pfmea_worksheet_row import PfmeaWorksheetRow
    from app.models.plant import Plant
    from app.models.process_item import ProcessItem
    from app.models.user import User
    from app.models.product_family import ProductFamily
    from app.models.production_line import ProductionLine


class PfmeaHeader(Base):
    """PFMEA document header — ties a FMEA analysis to an approved process flow.

    Extended for AIAG-VDA 2019 Step 1 compliance with project metadata,
    MOC status tracking, and downstream worksheet relationships.
    """

    __tablename__ = "pfmea_headers"
    __table_args__ = (Index("ix_pfmea_headers_flowchart_id", "flowchart_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    flowchart_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("flowcharts.id"),
        comment="Ties the FMEA to the approved process flow",
    )
    pfmea_id_number: Mapped[Optional[str]] = mapped_column(
        String, unique=True, comment="e.g. PUEBLA_PFMEA_001_2026_1"
    )

    # Step 1: Project metadata
    project_name: Mapped[Optional[str]] = mapped_column(Text)
    customer: Mapped[Optional[str]] = mapped_column(Text)
    original_launch_date: Mapped[Optional[date]] = mapped_column(Date)
    part_number: Mapped[Optional[str]] = mapped_column(Text)
    product_description: Mapped[Optional[str]] = mapped_column(Text)
    product_family_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("product_families.id"))
    production_line_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("production_lines.id"))

    # MOC status lifecycle
    moc_status: Mapped[str] = mapped_column(
        String,
        default="Draft",
        server_default="Draft",
        comment="Draft, In Review, Approved, Archived",
    )

    # Plant association
    plant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("plants.id")
    )

    # Original fields preserved
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    revision_date: Mapped[Optional[date]] = mapped_column(Date)
    confidentiality_level: Mapped[Optional[str]] = mapped_column(String)
    status: Mapped[Optional[str]] = mapped_column(
        String, comment="Draft, In Review, Approved, Archived"
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
    plant: Mapped[Optional["Plant"]] = relationship()
    product_family_rel: Mapped[Optional["ProductFamily"]] = relationship(back_populates="pfmea_headers")
    production_line_rel: Mapped[Optional["ProductionLine"]] = relationship(back_populates="pfmea_headers")
    team_members: Mapped[List["PfmeaTeamMember"]] = relationship(
        back_populates="pfmea", cascade="all, delete-orphan"
    )
    process_items: Mapped[List["ProcessItem"]] = relationship(
        back_populates="pfmea", cascade="all, delete-orphan"
    )
    worksheet_rows: Mapped[List["PfmeaWorksheetRow"]] = relationship(
        back_populates="pfmea",
        cascade="all, delete-orphan",
        order_by="PfmeaWorksheetRow.sequence_order",
        lazy="selectin",
    )
