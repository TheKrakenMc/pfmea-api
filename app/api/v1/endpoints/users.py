import string
import secrets
import logging
from typing import Any, List, Optional
from pydantic import BaseModel, EmailStr
from app.core.passwords import Password
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from app.core.db import get_db
from app.models.user import User
from app.models.role import Role
from app.models.plant import Plant
from app.core.hashing import hash_password
from app.api.deps import get_current_user, CurrentUser
from app.services.notification import send_welcome_email
from app.core.security import create_verification_token
from app.core.config import get_settings


settings = get_settings()

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Schemas ──────────────────────────────────────────────────────────────────
class UserLookup(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role_name: Optional[str] = None


class UserRead(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[str] = None
    role_name: Optional[str] = None
    department_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    must_change_password: bool


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: Password
    employment_position: Optional[str] = None


class AdminUserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role_name: str
    department_id: Optional[int] = None
    employment_position: Optional[str] = None


class AdminUserUpdate(BaseModel):
    full_name: str
    email: EmailStr
    role_name: str
    department_id: Optional[int] = None
    employment_position: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class UpdateRoleRequest(BaseModel):
    role_name: str  # Admin, PFMEA Owner, Team Member, Viewer


class UpdateStatusRequest(BaseModel):
    is_active: bool


# ─── Admin Check Dependency ───────────────────────────────────────────────────


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that verifies the current user exists and has the Administrator role.
    """
    stmt = select(User).where(User.id == int(current_user.id))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # Fetch role name
    if not user.role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: User has no assigned role",
        )

    stmt_role = select(Role).where(Role.id == user.role_id)
    res_role = await db.execute(stmt_role)
    role = res_role.scalars().first()

    if not role or role.name.lower() not in ["administrator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator role required",
        )

    return user


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/register", response_model=UserRead, summary="Registro público de nuevos usuarios"
)
async def register_user(
    register_data: UserRegister,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Registers a new user into the system.
    Default role is set to 'Viewer'.
    Primary plant is set to the first active plant in the database (since plant_id is not null).
    """
    # 1. Check if user already exists
    stmt = select(User).where(func.lower(User.email) == register_data.email.lower())
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # 2. Get default role 'Viewer'
    stmt_role = select(Role).where(func.lower(Role.name) == "viewer")
    res_role = await db.execute(stmt_role)
    viewer_role = res_role.scalars().first()
    if not viewer_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration error: Default 'Viewer' role not found",
        )

    # 3. Get default active plant
    stmt_plant = (
        select(Plant)
        .where(Plant.is_active.is_(True), Plant.id == db.info.get("plant_id"))
        .limit(1)
    )
    res_plant = await db.execute(stmt_plant)
    default_plant = res_plant.scalars().first()
    if not default_plant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration error: No active plant found in database",
        )

    # 4. Hash password with exactly 10 salts
    hashed_pwd = hash_password(register_data.password)

    # 5. Create user
    new_user = User(
        full_name=register_data.full_name,
        email=register_data.email.lower(),
        password_hash=hashed_pwd,
        role_id=viewer_role.id,
        plant_id=default_plant.id,
        employment_position=register_data.employment_position,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    return UserRead(
        id=str(new_user.id),
        full_name=new_user.full_name,
        email=new_user.email,
        role_id=str(new_user.role_id),
        role_name=viewer_role.name,
        department_id=str(new_user.department_id) if new_user.department_id else None,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        must_change_password=new_user.must_change_password,
    )


@router.get(
    "/lookup",
    response_model=List[UserLookup],
    summary="Búsqueda rápida de usuarios activos",
)
async def lookup_users(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Any:
    """
    Returns a lightweight list of all active system users.
    Accessible to any authenticated user.
    """
    stmt = (
        select(User)
        .options(joinedload(User.department), joinedload(User.role))
        .where(User.is_active.is_(True))
        .order_by(User.full_name.asc())
    )
    if current_user.role_name.lower() != "administrator":
        from app.models.auth_session import UserPlant

        stmt = stmt.where(
            User.id.in_(
                select(UserPlant.user_id).where(
                    UserPlant.plant_id == current_user.plant_id
                )
            )
        )
    res = await db.execute(stmt)
    users = res.scalars().all()

    return [
        UserLookup(
            id=str(u.id),
            full_name=u.full_name,
            email=u.email,
            department=u.department.name if u.department else None,
            role_name=u.role.name if u.role else None,
        )
        for u in users
    ]


@router.get(
    "/",
    response_model=List[UserRead],
    summary="Listado de usuarios (Exclusivo Administrador)",
)
async def list_users(
    admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Returns a list of all system users.
    Accessible only to system Administrators.
    """
    stmt = select(User).order_by(User.id.asc())
    res = await db.execute(stmt)
    users = res.scalars().all()

    output = []
    for u in users:
        role_name = "None"
        if u.role_id:
            role_stmt = select(Role).where(Role.id == u.role_id)
            role_res = await db.execute(role_stmt)
            role_obj = role_res.scalars().first()
            if role_obj:
                role_name = role_obj.name

        output.append(
            UserRead(
                id=str(u.id),
                full_name=u.full_name,
                email=u.email,
                role_id=str(u.role_id) if u.role_id else None,
                role_name=role_name,
                department_id=str(u.department_id) if u.department_id else None,
                is_active=u.is_active,
                is_verified=u.is_verified,
                must_change_password=u.must_change_password,
            )
        )
    return output


@router.post(
    "/admin", response_model=UserRead, summary="Crear usuario por administrador"
)
async def create_user_admin(
    user_data: AdminUserCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # 1. Check if user already exists
    stmt = select(User).where(func.lower(User.email) == user_data.email.lower())
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    # 2. Get active plant
    stmt_plant = select(Plant).where(Plant.is_active.is_(True)).limit(1)
    res_plant = await db.execute(stmt_plant)
    default_plant = res_plant.scalars().first()

    # 3. Get Role
    role_name = user_data.role_name
    if role_name.lower() == "admin":
        role_name = "Administrator"
    stmt_role = select(Role).where(func.lower(Role.name) == role_name.lower())
    res_role = await db.execute(stmt_role)
    new_role = res_role.scalars().first()
    if not new_role:
        raise HTTPException(
            status_code=400, detail=f"Role '{user_data.role_name}' does not exist"
        )

    # 4. Create User
    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email.lower(),
        password_hash=hashed_pwd,
        role_id=new_role.id,
        plant_id=default_plant.id if default_plant else None,
        department_id=user_data.department_id,
        employment_position=user_data.employment_position,
        is_active=True,
        is_verified=False,
        must_change_password=True,
    )
    db.add(new_user)
    await db.flush()

    from app.models.auth_session import UserPlant

    if new_user.plant_id:
        db.add(UserPlant(user_id=new_user.id, plant_id=new_user.plant_id))

    # Generate verification token and send email
    token = create_verification_token(new_user.email)
    frontend_url = settings.FRONTEND_URL
    verification_link = f"{frontend_url.strip('/')}/verify-email?token={token}"

    # Get department name for the email
    department_name = "Sin Departamento"
    if new_user.department_id:
        from app.models.department import Department

        dept_stmt = select(Department).where(Department.id == new_user.department_id)
        dept_res = await db.execute(dept_stmt)
        dept_obj = dept_res.scalars().first()
        if dept_obj:
            department_name = dept_obj.name

    import asyncio

    asyncio.create_task(
        send_welcome_email(
            to_email=new_user.email,
            temp_password=user_data.password,
            role_name=new_role.name,
            department_name=department_name,
            verification_link=verification_link,
        )
    )

    return UserRead(
        id=str(new_user.id),
        full_name=new_user.full_name,
        email=new_user.email,
        role_id=str(new_user.role_id),
        role_name=new_role.name,
        department_id=str(new_user.department_id) if new_user.department_id else None,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        must_change_password=new_user.must_change_password,
    )


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Actualizar usuario por administrador",
)
async def update_user_admin(
    user_id: int,
    user_data: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # 1. Fetch user
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user_to_update = res.scalars().first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check email uniqueness
    stmt_email = select(User).where(
        func.lower(User.email) == user_data.email.lower(), User.id != user_id
    )
    res_email = await db.execute(stmt_email)
    if res_email.scalars().first():
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )

    # 3. Get Role
    role_name = user_data.role_name
    if role_name.lower() == "admin":
        role_name = "Administrator"
    stmt_role = select(Role).where(func.lower(Role.name) == role_name.lower())
    res_role = await db.execute(stmt_role)
    new_role = res_role.scalars().first()
    if not new_role:
        raise HTTPException(
            status_code=400, detail=f"Role '{user_data.role_name}' does not exist"
        )

    user_to_update.full_name = user_data.full_name
    if user_to_update.email.lower() != user_data.email.lower():
        user_to_update.is_verified = False
    user_to_update.email = user_data.email.lower()
    from app.services.session_service import revoke_user_sessions

    await revoke_user_sessions(db, user_to_update.id)
    user_to_update.role_id = new_role.id
    user_to_update.department_id = user_data.department_id
    user_to_update.employment_position = user_data.employment_position

    await db.flush()

    return UserRead(
        id=str(user_to_update.id),
        full_name=user_to_update.full_name,
        email=user_to_update.email,
        role_id=str(user_to_update.role_id),
        role_name=new_role.name,
        department_id=str(user_to_update.department_id)
        if user_to_update.department_id
        else None,
        is_active=user_to_update.is_active,
        is_verified=user_to_update.is_verified,
        must_change_password=user_to_update.must_change_password,
    )


@router.put(
    "/{user_id}/role",
    response_model=UserRead,
    summary="Actualizar rol técnico (Exclusivo Administrador)",
)
async def update_user_role(
    user_id: int,
    role_data: UpdateRoleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Updates the technical role of a user.
    Options: Admin, PFMEA Owner, Team Member, Viewer.
    """
    # 1. Fetch user to update
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user_to_update = res.scalars().first()

    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # 2. Normalize and look up role
    role_name = role_data.role_name
    if role_name.lower() == "admin":
        role_name = "Administrator"

    stmt_role = select(Role).where(func.lower(Role.name) == role_name.lower())
    res_role = await db.execute(stmt_role)
    new_role = res_role.scalars().first()

    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.role_name}' does not exist",
        )

    # 3. Update role
    user_to_update.role_id = new_role.id
    await db.flush()

    return UserRead(
        id=str(user_to_update.id),
        full_name=user_to_update.full_name,
        email=user_to_update.email,
        role_id=str(user_to_update.role_id),
        role_name=new_role.name,
        department_id=str(user_to_update.department_id)
        if user_to_update.department_id
        else None,
        is_active=user_to_update.is_active,
        is_verified=user_to_update.is_verified,
        must_change_password=user_to_update.must_change_password,
    )


@router.put(
    "/{user_id}/status",
    response_model=UserRead,
    summary="Activar/Inactivar usuario (Exclusivo Administrador)",
)
async def update_user_status(
    user_id: int,
    status_data: UpdateStatusRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Toggles the active status of a user.
    If inactivated (is_active=False), prepends "ARCHIVED " to their full_name in the DB
    to track history under TISAX regulations.
    If reactivated, removes the "ARCHIVED " prefix.
    """
    # 1. Fetch user
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user_to_update = res.scalars().first()

    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent admin from inactivating themselves
    if user_to_update.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account",
        )

    # 2. Toggle active and alter full_name
    original_name = user_to_update.full_name or ""

    if not status_data.is_active:
        # Deactivating: Prepend 'ARCHIVED ' if not already prepended
        if not original_name.startswith("ARCHIVED "):
            user_to_update.full_name = f"ARCHIVED {original_name}"
        user_to_update.is_active = False
        from app.services.session_service import revoke_user_sessions

        await revoke_user_sessions(db, user_to_update.id)
    else:
        # Activating: Remove 'ARCHIVED ' prefix if present
        if original_name.startswith("ARCHIVED "):
            user_to_update.full_name = original_name.replace("ARCHIVED ", "", 1)
        user_to_update.is_active = True

    await db.flush()

    # Get role name for return object
    role_name = "None"
    if user_to_update.role_id:
        r_stmt = select(Role).where(Role.id == user_to_update.role_id)
        r_res = await db.execute(r_stmt)
        r_obj = r_res.scalars().first()
        if r_obj:
            role_name = r_obj.name

    return UserRead(
        id=str(user_to_update.id),
        full_name=user_to_update.full_name,
        email=user_to_update.email,
        role_id=str(user_to_update.role_id) if user_to_update.role_id else None,
        role_name=role_name,
        department_id=str(user_to_update.department_id)
        if user_to_update.department_id
        else None,
        is_active=user_to_update.is_active,
        is_verified=user_to_update.is_verified,
        must_change_password=user_to_update.must_change_password,
    )


@router.post(
    "/{user_id}/resend-verification",
    summary="Reenviar link de verificación (Exclusivo Administrador)",
)
async def resend_verification_admin(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Resends the verification email with a new 24-hour token.
    Only for unverified users.
    """
    # 1. Fetch user
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    # Get role name
    role_name = "Viewer"
    if user.role_id:
        stmt_role = select(Role).where(Role.id == user.role_id)
        res_role = await db.execute(stmt_role)
        role_obj = res_role.scalars().first()
        if role_obj:
            role_name = role_obj.name

    # Get department name
    department_name = "Sin Departamento"
    if user.department_id:
        from app.models.department import Department

        dept_stmt = select(Department).where(Department.id == user.department_id)
        dept_res = await db.execute(dept_stmt)
        dept_obj = dept_res.scalars().first()
        if dept_obj:
            department_name = dept_obj.name

    # Generate new temporary password
    from app.core.hashing import hash_password

    chars = string.ascii_letters + string.digits
    temp_pwd = "".join(secrets.choice(chars) for _ in range(10))
    hashed_pwd = hash_password(temp_pwd)

    from app.services.session_service import revoke_user_sessions

    await revoke_user_sessions(db, user.id)
    user.password_hash = hashed_pwd
    user.must_change_password = True
    await db.flush()

    token = create_verification_token(user.email)
    frontend_url = settings.FRONTEND_URL
    verification_link = f"{frontend_url.strip('/')}/verify-email?token={token}"

    import asyncio

    asyncio.create_task(
        send_welcome_email(
            to_email=user.email,
            temp_password=temp_pwd,
            role_name=role_name,
            department_name=department_name,
            verification_link=verification_link,
        )
    )

    return {"message": "Verification email resent successfully"}


class PlantAssignments(BaseModel):
    plant_ids: list[int]
    primary_plant_id: int


@router.put("/{user_id}/plants")
async def assign_plants(
    user_id: int,
    payload: PlantAssignments,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth_session import UserPlant
    from app.services.session_service import revoke_user_sessions
    from sqlalchemy import delete

    user = await db.get(User, user_id)
    ids = set(payload.plant_ids)
    if not user:
        raise HTTPException(404, "User not found")
    if payload.primary_plant_id not in ids or not ids:
        raise HTTPException(400, "Primary plant must be assigned")
    valid = set(
        (
            await db.scalars(
                select(Plant.id).where(Plant.id.in_(ids), Plant.is_active.is_(True))
            )
        ).all()
    )
    if valid != ids:
        raise HTTPException(400, "Unknown or inactive plant")
    await db.execute(delete(UserPlant).where(UserPlant.user_id == user_id))
    for plant_id in sorted(ids):
        db.add(UserPlant(user_id=user_id, plant_id=plant_id))
    user.plant_id = payload.primary_plant_id
    await revoke_user_sessions(db, user_id)
    await db.flush()
    return {"plant_ids": sorted(ids), "primary_plant_id": user.plant_id}


@router.get("/{user_id}/plants")
async def get_assignments(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.models.auth_session import UserPlant

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    ids = list(
        (
            await db.scalars(
                select(UserPlant.plant_id).where(UserPlant.user_id == user_id)
            )
        ).all()
    )
    return {"plant_ids": ids, "primary_plant_id": user.plant_id}
