from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class TechnologyCategory(Base):
    """Categories for technologies."""

    __tablename__ = "technology_categories"
    __table_args__ = (
        UniqueConstraint(
            "name", name="uq_technology_categories_name"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True, comment="Category Name")
    description: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
