from typing import List
from fastapi import Request, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.security import verify_access_token
from app.core.db import get_db
from app.models.user import User


class CurrentUser(BaseModel):
    """Lightweight representation of the authenticated user."""

    model_config = {"from_attributes": True}

    id: int
    role_id: int
    role_name: str
    must_change_password: bool
    is_verified: bool
    plant_id: int | None = None
    plant_ids: list[int] = []


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """
    Extract and validate JWT from the HttpOnly cookie.
    Returns a CurrentUser with resolved role name for RBAC checks.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Optional: strip "Bearer " if it's included in the cookie value
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        role_id = payload.get("role_id")

        if user_id is None or role_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        from datetime import datetime, timezone
        from app.models.auth_session import AuthSession, UserPlant
        from app.services.session_service import utc
        import secrets

        auth_session = await db.get(AuthSession, payload.get("sid"))
        if (
            not auth_session
            or auth_session.revoked
            or str(auth_session.user_id) != str(user_id)
            or utc(auth_session.expires_at) <= datetime.now(timezone.utc)
        ):
            raise HTTPException(status_code=401, detail="Session revoked or expired")
        if request.method not in {
            "GET",
            "HEAD",
            "OPTIONS",
        } and not secrets.compare_digest(
            auth_session.csrf_token, request.headers.get("x-csrf-token", "")
        ):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
        request.state.session_id = auth_session.id
        # Verify user in database and eagerly load role
        stmt = (
            select(User).options(selectinload(User.role)).where(User.id == int(user_id))
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active or user.deleted_at is not None or not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        allowed_paths = [
            "/api/v1/auth/change-password",
            "/api/v1/auth/logout",
            "/api/v1/auth/me",
        ]
        if user.must_change_password and not any(
            request.url.path.endswith(p) for p in allowed_paths
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PASSWORD_CHANGE_REQUIRED",
            )

        role_name = user.role.name if user.role else "Unknown"
        if role_name.lower() == "admin":
            role_name = "Administrator"
        from app.models import Plant
        plant_ids = list(
            (
                await db.scalars(
                    select(UserPlant.plant_id).join(Plant,Plant.id==UserPlant.plant_id).where(UserPlant.user_id == user.id,Plant.is_active.is_(True))
                )
            ).all()
        )
        if role_name.lower()=="administrator":
            plant_ids=list((await db.scalars(select(Plant.id).where(Plant.is_active.is_(True)))).all())
        raw_plant = request.headers.get("x-plant-id")
        try:
            selected_plant = (
                int(raw_plant)
                if raw_plant
                else (user.plant_id if user.plant_id in plant_ids else (min(plant_ids) if plant_ids else None))
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid plant selection")
        if selected_plant is not None:
            from app.models.plant import Plant

            plant = await db.get(Plant, selected_plant)
            if (
                not plant
                or not plant.is_active
                or (
                    role_name.lower() != "administrator"
                    and selected_plant not in plant_ids
                )
            ):
                raise HTTPException(status_code=403, detail="Plant access denied")
        if selected_plant is None and not request.url.path.startswith("/api/v1/auth/"):
            raise HTTPException(403,"No authorized active plant")
        request.state.plant_id = selected_plant
        db.info["current_user_id"] = user.id
        db.info["role_name"] = role_name.lower()
        db.info["plant_id"] = selected_plant
        db.info["plant_ids"] = plant_ids
        if db.bind.dialect.name == "postgresql":
            from sqlalchemy import text

            await db.execute(
                text(
                    "SELECT set_config('app.current_plant_id', :plant, true), set_config('app.current_user_id', :actor, true), set_config('app.is_admin', :admin, true)"
                ),
                {
                    "plant": str(selected_plant or 0),
                    "actor": str(user.id),
                    "admin": str(role_name.lower() == "administrator").lower(),
                },
            )
        request.state.current_user_id = user.id
        return CurrentUser(
            id=user.id,
            role_id=user.role_id or 0,
            role_name=role_name,
            must_change_password=user.must_change_password,
            is_verified=user.is_verified,
            plant_id=selected_plant,
            plant_ids=plant_ids,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


class RoleChecker:
    """
    Dependency that verifies the current user has one of the allowed roles.
    Compares role **names** (case-insensitive) resolved from the database.

    Usage::

        Depends(RoleChecker(["Administrator", "PFMEA Owner"]))
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [r.lower() for r in allowed_roles]

    async def __call__(
        self,
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if user.role_name.lower() not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return user


def get_plant_id(request: Request) -> int | None:
    """
    Extract plant_id from the X-Plant-Id header.
    Returns None if not provided or invalid.
    """
    plant_id = request.headers.get("x-plant-id")
    if plant_id and plant_id.isdigit():
        return int(plant_id)
    return None


class PfmeaAccessChecker:
    """TISAX-compliant per-analysis access control.

    Validates that the current user can access a specific PFMEA analysis
    based on both their **system role** and their **team membership**.

    Access hierarchy:
    - ``Administrator``: full control on all analyses.
    - ``PFMEA Owner`` (system role): full control on all analyses.
    - ``Team Member`` (system role): only analyses where they are in
      ``pfmea_team_members`` with ``role_in_team`` in
      ('PFMEA Owner', 'Team Member').
    - ``Viewer``: read-only on assigned analyses.

    Usage::

        @router.patch("/{pfmea_id}/worksheet/{row_id}")
        async def update_row(
            pfmea_id: int,
            ...,
            user: CurrentUser = Depends(PfmeaAccessChecker(require_write=True)),
        ):
    """

    # System roles that have unrestricted PFMEA access
    ADMIN_ROLES = {"administrator", "pfmea owner"}

    def __init__(self, require_write: bool = False):
        self.require_write = require_write

    async def __call__(
        self,
        pfmea_id: int,
        user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        from app.api.access import check_pfmea

        await check_pfmea(db, user, pfmea_id, self.require_write)
        return user
