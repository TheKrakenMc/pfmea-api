"""Password authentication, revocable sessions and single-use account recovery."""

import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel, EmailStr, Field
from app.core.passwords import Password
from app.core.db import get_db
from app.models.user import User
from app.models.user_otp import UserOTP
from app.models.auth_session import AuthSession, UserPlant
from app.core.security import verify_refresh_token, limiter, settings
from app.core.hashing import verify_password, hash_password
from app.api.deps import get_current_user, CurrentUser
import hashlib
import hmac
from app.services.session_service import (
    issue_session,
    revoke_user_sessions,
    digest,
    utc,
)


_DUMMY_HASH = hash_password(secrets.token_urlsafe(24))


def recovery_digest(code: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        ("password-reset:" + code).encode(),
        hashlib.sha256,
    ).hexdigest()


router = APIRouter()
logger = logging.getLogger(__name__)


class UserRead(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_id: str
    role_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    is_verified: bool
    must_change_password: bool
    plant_id: Optional[int] = None
    plant_ids: list[int] = []
    csrf_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


async def profile(db, user, session):
    await db.refresh(user, attribute_names=["role", "department"])
    from app.models.plant import Plant

    if user.role and user.role.name.lower() in {"administrator", "admin"}:
        plant_ids = list(
            (await db.scalars(select(Plant.id).where(Plant.is_active.is_(True)))).all()
        )
    else:
        plant_ids = list(
            (
                await db.scalars(
                    select(UserPlant.plant_id).join(Plant,Plant.id==UserPlant.plant_id).where(UserPlant.user_id == user.id,Plant.is_active.is_(True))
                )
            ).all()
        )
    return UserRead(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        role_id=str(user.role_id or 0),
        role_name=(
            "Administrator" if user.role.name.lower() == "admin" else user.role.name
        )
        if user.role
        else None,
        department=user.department.name if user.department else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        must_change_password=user.must_change_password,
        plant_id=user.plant_id if user.plant_id in plant_ids else (min(plant_ids) if plant_ids else None),
        plant_ids=plant_ids,
        csrf_token=session.csrf_token,
    )


@router.get("/me", response_model=UserRead)
async def get_me(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, current_user.id)
    session = await db.get(AuthSession, request.state.session_id)
    return await profile(db, user, session)


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.scalars(
            select(User).where(func.lower(User.email) == login_data.email.lower())
        )
    ).first()
    valid = verify_password(
        login_data.password,
        user.password_hash if user and user.password_hash else _DUMMY_HASH,
    )
    if (
        not valid
        or user is None
        or not user.is_active
        or not user.is_verified
        or user.deleted_at is not None
    ):
        raise HTTPException(status_code=401, detail="Incorrect email or credentials")
    session = await issue_session(db, user, response)
    return {
        "message": "Successfully authenticated",
        "user": await profile(db, user, session),
        "csrf_token": session.csrf_token,
    }


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh_token(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("refresh_token", "")
    try:
        payload = verify_refresh_token(token)
        session_id = payload["sid"]
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    session = (
        await db.scalars(
            select(AuthSession).where(AuthSession.id == session_id).with_for_update()
        )
    ).first()
    if (
        not session
        or session.revoked
        or utc(session.expires_at) <= datetime.now(timezone.utc)
        or session.user_id != user_id
    ):
        raise HTTPException(status_code=401, detail="Session expired")
    if not secrets.compare_digest(
        session.csrf_token, request.headers.get("x-csrf-token", "")
    ):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    if not secrets.compare_digest(session.refresh_hash, digest(token)):
        session.revoked = True
        await db.commit()  # Revocation must survive the rejected request.
        raise HTTPException(
            status_code=401, detail="Refresh token reused; session revoked"
        )
    user = await db.get(User, user_id)
    if (
        not user
        or not user.is_active
        or not user.is_verified
        or user.deleted_at is not None
    ):
        session.revoked = True
        await db.commit()
        raise HTTPException(status_code=401, detail="Session revoked")
    await issue_session(db, user, response, session)
    return {"message": "Token successfully refreshed", "csrf_token": session.csrf_token}


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await db.get(AuthSession, request.state.session_id)
    session.revoked = True
    secure = settings.ENVIRONMENT.lower() in {"production", "staging", "secure"}
    for name in ["access_token", "refresh_token", "csrf_token"]:
        response.delete_cookie(
            name,
            path="/",
            secure=secure,
            httponly=name != "csrf_token",
            samesite="none" if secure else "lax",
        )
    return {"message": "Successfully logged out"}


class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/verify-email", summary="Verificar cuenta mediante enlace de correo")
async def verify_email_endpoint(
    request_data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    from app.core.security import verify_verification_token

    try:
        email = verify_verification_token(request_data.token)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification token"
        )

    stmt = select(User).where(func.lower(User.email) == email.lower()).with_for_update()
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from app.models.auth_session import UsedVerificationToken
    from app.services.session_service import digest

    token_hash = digest(request_data.token)
    if await db.get(UsedVerificationToken, token_hash) or user.is_verified:
        raise HTTPException(
            status_code=400, detail="Verification token already consumed"
        )
    db.add(UsedVerificationToken(token_hash=token_hash, user_id=user.id))

    user.is_verified = True
    await db.flush()
    return {"message": "Email successfully verified"}


class ChangePasswordRequest(BaseModel):
    new_password: Password


@router.post("/change-password", summary="Cambio obligatorio de contraseña")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = select(User).where(User.id == current_user.id)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from app.core.hashing import hash_password

    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters long"
        )

    user.password_hash = hash_password(password_data.new_password)
    user.must_change_password = False
    await revoke_user_sessions(db, user.id)
    await db.flush()

    return {"message": "Password changed successfully"}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password", summary="Solicitar restablecimiento de contraseña")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(User).where(func.lower(User.email) == data.email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        # We return success anyway to prevent email enumeration
        return {
            "message": "If the email is registered, you will receive an OTP code to reset your password."
        }

    if not user.is_active:
        return {
            "message": "If the email is registered, you will receive an OTP code to reset your password."
        }

    # Generate random 6-digit numeric OTP
    otp = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    await db.execute(
        update(UserOTP).where(UserOTP.user_id == user.id).values(is_used=True)
    )
    # Store only a purpose-bound hash. Legacy plaintext codes are invalidated by migration.
    db_otp = UserOTP(
        user_id=user.id,
        otp_code=recovery_digest(otp),
        expires_at=expires_at,
        is_used=False,
    )
    db.add(db_otp)
    await db.flush()

    # Send OTP
    from app.services.notification import send_reset_password_otp_email
    import asyncio

    asyncio.create_task(send_reset_password_otp_email(user.email, otp))

    return {
        "message": "If the email is registered, you will receive an OTP code to reset your password."
    }


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(pattern=r"^\d{6}$")
    new_password: Password


@router.post("/reset-password", summary="Restablecer contraseña con OTP")
@limiter.limit("5/minute")
async def reset_password(
    request: Request, data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(User).where(func.lower(User.email) == data.email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request"
        )

    # Find active and matching OTP
    stmt_otp = (
        select(UserOTP)
        .where(UserOTP.user_id == user.id)
        .where(UserOTP.is_used.is_(False))
        .with_for_update()
        .order_by(UserOTP.created_at.desc())
        .limit(1)
    )
    res_otp = await db.execute(stmt_otp)
    db_otp = res_otp.scalars().first()

    if not db_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code"
        )

    if db_otp.attempts >= 5 or not secrets.compare_digest(
        db_otp.otp_code, recovery_digest(data.otp_code)
    ):
        db_otp.attempts += 1
        if db_otp.attempts >= 5:
            db_otp.is_used = True
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid verification code")

    if db_otp.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has already been used",
        )

    expires_at = db_otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired (5-minute limit)",
        )

    from app.core.hashing import hash_password

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Update password and mark OTP as used
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    db_otp.is_used = True
    await revoke_user_sessions(db, user.id)
    await db.flush()

    return {"message": "Password has been successfully reset. You can now log in."}


@router.get("/csrf")
async def csrf_bootstrap(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token", "")
    try:
        payload = verify_refresh_token(token)
        session = await db.get(AuthSession, payload["sid"])
    except (ValueError, KeyError):
        raise HTTPException(401, "No active session")
    if (
        not session
        or session.revoked
        or utc(session.expires_at) <= datetime.now(timezone.utc)
        or not secrets.compare_digest(session.refresh_hash, digest(token))
    ):
        raise HTTPException(401, "No active session")
    return {"csrf_token": session.csrf_token}
