"""Revocable sessions and explicit user-to-plant assignments."""

from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    refresh_hash: Mapped[str] = mapped_column(String(64))
    csrf_token: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class UserPlant(Base):
    __tablename__ = "user_plants"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), primary_key=True)


class UsedVerificationToken(Base):
    __tablename__ = "used_verification_tokens"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
