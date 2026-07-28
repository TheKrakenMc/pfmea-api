"""DocumentVersion model — polymorphic version tracking for all document types."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class DocumentVersion(Base):
    """Centralised revision table replacing the three per-entity revision tables.

    ``document_type`` is one of ``'flowchart'``, ``'control_plan'``,
    or ``'operation_instruction'``.
    """

    __tablename__ = "document_versions"
    __table_args__ = (
        Index("ix_doc_versions_type_id", "document_type", "document_id"),
        Index("ix_doc_versions_created_at", "created_at"),
        Index("ix_doc_versions_created_by", "created_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    change_reason: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    original_creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observations: Mapped[Optional[str]] = mapped_column(String)
    snapshot_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_initial_revision: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by])
