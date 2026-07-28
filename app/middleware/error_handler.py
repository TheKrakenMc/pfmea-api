"""Standardised error-handling decorator for FastAPI route handlers.

Wraps an endpoint so that:
* ``HTTPException`` is re-raised untouched (FastAPI already serialises it).
* ``RequestValidationError`` is re-raised for FastAPI's built-in handler.
* Any other ``Exception`` is caught, logged with full traceback, and
  returned as a JSON 500 response with a consistent envelope.

Usage::

    @router.get("/items/{id}")
    @error_handler
    async def get_item(id: int, db=Depends(get_db)):
        ...
"""

from __future__ import annotations

import functools
import logging
import traceback
import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger("pfmea.errors")


def error_handler(func):
    """Decorator: capture unhandled exceptions and return a standardised JSON envelope."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Try to extract request_id from the Request object (if present in kwargs)
        request_id = str(uuid.uuid4())
        for arg in args:
            if isinstance(arg, Request):
                request_id = getattr(arg.state, "request_id", request_id)
                break
        request_obj = kwargs.get("request")
        if isinstance(request_obj, Request):
            request_id = getattr(request_obj.state, "request_id", request_id)

        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise  # Re-raise FastAPI HTTP errors as-is
        except RequestValidationError:
            raise  # Let FastAPI's built-in handler format these
        except Exception as exc:
            settings = get_settings()
            logger.error(
                "Unhandled error in %s: %s",
                func.__name__,
                exc,
                exc_info=True,
                extra={"traceback": traceback.format_exc()},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "detail": str(exc) if settings.DEBUG else None,
                        "request_id": request_id,
                    },
                },
            )

    return wrapper
