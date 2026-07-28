"""Reusable soft-delete mixin for SQLAlchemy models.

Adds ``deleted_at`` and ``deleted_by`` columns alongside the existing
``is_active`` flag.  Provides a helper ``soft_delete()`` method so that
callers never need to remember the correct set of field mutations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    """Mixin that provides universal soft-delete columns and helper.

    Usage::

        class MyModel(Base, SoftDeleteMixin):
            ...

    Then call ``instance.soft_delete(user_id=current_user.id)`` instead
    of ``db.delete(instance)``.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        default=None,
        index=False,  # partial index created in migration
    )
    deleted_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        default=None,
    )

    # noinspection PyUnresolvedReferences
    def soft_delete(self, user_id: int) -> None:
        """Mark this record as logically deleted."""
        self.is_active = False  # type: ignore[attr-defined]
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    # noinspection PyUnresolvedReferences
    def restore(self) -> None:
        """Undo a soft-delete."""
        self.is_active = True  # type: ignore[attr-defined]
        self.deleted_at = None
        self.deleted_by = None
