from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins.soft_delete import SoftDeleteMixin

class InstructionSheet(Base, SoftDeleteMixin):
    __tablename__ = "instruction_sheets"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
