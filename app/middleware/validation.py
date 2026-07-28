"""Validation helpers for FastAPI endpoints.

FastAPI already performs Pydantic model validation automatically for
request bodies.  This module provides **additional** utilities:

* ``validate_schema`` — decorator for adding business-rule validators
  on top of Pydantic's structural validation.
* ``ValidatedQuery`` — dependency helper for strongly-typed query params.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Optional, Type

from fastapi import HTTPException, Query, status
from pydantic import BaseModel, ValidationError


def validate_schema(schema_class: Type[BaseModel]):
    """Decorator that runs extra Pydantic validation after FastAPI's auto-parse.

    Use for business-rule validators that go beyond structural checks,
    e.g. ensuring ``rpn == severity * occurrence * detection``.

    Usage::

        @router.post("/failure-modes")
        @validate_schema(FailureModeCreate)
        async def create_failure_mode(payload: FailureModeCreate, ...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Locate the payload argument by matching schema_class
            for key, val in kwargs.items():
                if isinstance(val, schema_class):
                    try:
                        # Re-validate to trigger custom model_validators
                        schema_class.model_validate(val.model_dump())
                    except ValidationError as exc:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=exc.errors(),
                        )
                    break
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class PaginationParams(BaseModel):
    """Reusable pagination query-parameter set."""

    skip: int = 0
    limit: int = 50

    @classmethod
    def as_dependency(
        cls,
        skip: int = Query(0, ge=0, description="Rows to skip"),
        limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    ) -> "PaginationParams":
        return cls(skip=skip, limit=limit)


class DateRangeParams(BaseModel):
    """Reusable date-range query-parameter set for audit filters."""

    date_from: Optional[str] = None
    date_to: Optional[str] = None

    @classmethod
    def as_dependency(
        cls,
        date_from: Optional[str] = Query(None, description="Start date (ISO 8601)"),
        date_to: Optional[str] = Query(None, description="End date (ISO 8601)"),
    ) -> "DateRangeParams":
        return cls(date_from=date_from, date_to=date_to)
