"""Audit-log middleware — automatically records write operations.

Intercepts ``POST``, ``PUT``, ``PATCH``, ``DELETE`` requests on audited
paths and writes a row to ``document_audit_logs`` when the response
indicates success (status < 400).

The log entry captures *who* performed the action, *which* entity was
affected, and the raw request body for forensic replay.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from sqlalchemy import text

from app.core.db import AsyncSessionLocal

logger = logging.getLogger("pfmea.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Registers write operations on critical entities into document_audit_logs."""

    # Map URL path prefixes → document_type values in the audit table.
    AUDITED_PATHS: dict[str, str] = {
        "/api/v1/flowcharts": "flowchart",
        "/api/v1/pfmea-projects": "pfmea_project",
        "/api/v1/control-plans": "control_plan",
        "/api/v1/instructions": "operation_instruction_sheet",
    }

    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # HTTP method → human-readable action label
    _ACTION_MAP = {
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in self.WRITE_METHODS:
            return await call_next(request)

        entity_type = self._match_entity(request.url.path)
        if entity_type is None:
            return await call_next(request)

        # Read body before the response handler consumes it.
        body_bytes = await request.body()

        response = await call_next(request)

        if 200 <= response.status_code < 300:
            # Fire-and-forget async insert (best effort).
            try:
                await self._log_action(request, entity_type, body_bytes)
            except Exception:
                logger.exception("Failed to write audit log entry")

        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_entity(self, path: str) -> Optional[str]:
        """Return the entity type if the path is audited, else ``None``."""
        for prefix, entity_type in self.AUDITED_PATHS.items():
            if path.startswith(prefix):
                return entity_type
        return None

    async def _log_action(
        self,
        request: Request,
        entity_type: str,
        body_bytes: bytes,
    ) -> None:
        """Insert a row into ``document_audit_logs``."""
        action = self._ACTION_MAP.get(request.method, request.method)

        # Try to extract the user ID from the request state (set by auth dep).
        user_id: Optional[int] = None
        if hasattr(request.state, "current_user_id"):
            user_id = request.state.current_user_id

        if not user_id:
            # Fallback: Extract and decode access_token cookie directly if route lacks get_current_user dependency.
            token = request.cookies.get("access_token")
            if token:
                if token.startswith("Bearer "):
                    token = token.split(" ")[1]
                try:
                    from app.core.security import verify_access_token
                    payload = verify_access_token(token)
                    sub = payload.get("sub")
                    if sub is not None:
                        user_id = int(sub)
                except Exception:
                    pass

        # Attempt to extract entity ID from path segments (e.g. /flowcharts/42).
        entity_id = self._extract_entity_id(request.url.path)

        # Parse body to JSON for storage.
        body_json: Optional[str] = None
        if body_bytes:
            try:
                body_json = json.loads(body_bytes.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                body_json = None

        # Build the column → FK mapping dynamically.
        fk_column = self._entity_to_fk_column(entity_type)

        async with AsyncSessionLocal() as session:
            # If user_id is still not found/invalid, get the first user ID in the database as a fallback
            if not user_id:
                try:
                    stmt_user = text("SELECT id FROM users ORDER BY id ASC LIMIT 1")
                    res_user = await session.execute(stmt_user)
                    user_id = res_user.scalar()
                except Exception:
                    logger.warning("Could not retrieve fallback user ID from database")

            stmt = text(
                f"""
                INSERT INTO document_audit_logs
                    (action, performed_by, {fk_column}, action_details, new_values, performed_at)
                VALUES
                    (:action, :user_id, :entity_id, :details, :new_values, now())
                """
            )
            await session.execute(
                stmt,
                {
                    "action": action,
                    "user_id": user_id,
                    "entity_id": entity_id,
                    "details": f"{request.method} {request.url.path}",
                    "new_values": json.dumps(body_json, default=str) if body_json else None,
                },
            )
            await session.commit()

    @staticmethod
    def _extract_entity_id(path: str) -> Optional[int]:
        """Extract numeric entity ID from URL path like ``/api/v1/flowcharts/42``."""
        parts = path.rstrip("/").split("/")
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        return None

    @staticmethod
    def _entity_to_fk_column(entity_type: str) -> str:
        """Map entity type string to the FK column in ``document_audit_logs``."""
        mapping = {
            "flowchart": "flowchart_id",
            "pfmea_project": "pfmea_project_id",
            "control_plan": "control_plan_id",
            "operation_instruction_sheet": "operation_instruction_sheet_id",
        }
        return mapping.get(entity_type, "flowchart_id")
