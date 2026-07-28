from typing import List
from fastapi import Request, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import verify_access_token
from app.core.db import get_db
from app.models.user import User
from app.models.role import Role


class CurrentUser(BaseModel):
    """Lightweight representation of the authenticated user."""
    model_config = {"from_attributes": True}

    id: int
    role_id: int
    role_name: str
    must_change_password: bool
    is_verified: bool


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> CurrentUser:
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

        # Verify user in database and eagerly load role
        stmt = select(User).options(selectinload(User.role)).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        allowed_paths = ["/api/v1/auth/change-password", "/api/v1/auth/logout", "/api/v1/auth/me"]
        if user.must_change_password and not any(request.url.path.endswith(p) for p in allowed_paths):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PASSWORD_CHANGE_REQUIRED",
            )

        role_name = user.role.name if user.role else "Unknown"
        request.state.current_user_id = user.id
        return CurrentUser(
            id=user.id,
            role_id=user.role_id or 0,
            role_name=role_name,
            must_change_password=user.must_change_password,
            is_verified=user.is_verified,
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
        role_lower = user.role_name.lower()

        # Admins and PFMEA Owners have unrestricted access
        if role_lower in self.ADMIN_ROLES:
            return user

        # For other roles, check team membership
        from app.models.pfmea_team_member import PfmeaTeamMember

        stmt = select(PfmeaTeamMember).where(
            PfmeaTeamMember.pfmea_id == pfmea_id,
            PfmeaTeamMember.user_id == user.id,
        )
        result = await db.execute(stmt)
        membership = result.scalars().first()

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this PFMEA team.",
            )

        # If write access is required, verify team role allows it
        if self.require_write:
            if membership.role_in_team == "Viewer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Viewers cannot modify PFMEA data.",
                )

        return user

