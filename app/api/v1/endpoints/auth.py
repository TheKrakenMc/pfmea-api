import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, EmailStr

from app.core.db import get_db
from app.models.user import User
from app.models.user_otp import UserOTP
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    limiter,
    settings
)
from app.core.hashing import verify_password
from app.api.deps import get_current_user, CurrentUser
from app.services.notification import send_otp_email

router = APIRouter()
logger = logging.getLogger(__name__)

# ─── Schemas ──────────────────────────────────────────────────────────────────

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

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str

# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserRead, summary="Obtener usuario actual")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get profile details of the currently logged in user.
    Reads the JWT from the secure HttpOnly cookie.
    """
    stmt = select(User).options(joinedload(User.role), joinedload(User.department)).where(User.id == int(current_user.id))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserRead(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        role_id=str(user.role_id) if user.role_id else "0",
        role_name=user.role.name if user.role else None,
        department=user.department.name if user.department else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        must_change_password=user.must_change_password,
    )


@router.post("/login", summary="Fase 1: Verificación de Credenciales y Envío de OTP")
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Phase 1 of Authentication: Validates email and password,
    then generates a secure random 6-digit OTP and triggers the email dispatch.
    """
    # 1. Fetch user by email
    stmt = select(User).where(func.lower(User.email) == login_data.email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.password_hash:
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or credentials"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user. Contact your Administrator."
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address first. Check your inbox for the verification link."
        )

    # 2. Verify password with bcrypt (constant time)
    if not verify_password(login_data.password, user.password_hash):
        logger.warning(f"Invalid password for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or credentials"
        )

    # 3. Generate random 6-digit numeric OTP
    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Store OTP in DB (single-use)
    db_otp = UserOTP(
        user_id=user.id,
        otp_code=otp,
        expires_at=expires_at,
        is_used=False
    )
    db.add(db_otp)
    await db.flush()

    # 4. Trigger Email notification asynchronously
    email_sent = await send_otp_email(user.email, otp)
    if not email_sent:
        logger.error(f"Failed to send OTP email to {user.email}")
        # Even if SMTP fails, we allow local testing through logs/console fallback print.

    return {
        "message": "OTP verification code sent to your email",
        "otp_required": True,
        "email": user.email
    }


@router.post("/verify-otp", summary="Fase 2: Verificación de OTP e Inicio de Sesión")
async def verify_otp(
    response: Response,
    otp_data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Phase 2 of Authentication: Validates the single-use OTP.
    On success, issues Access and Refresh tokens and stores them in secure HTTP-Only cookies.
    """
    # 1. Fetch user by email
    stmt = select(User).options(joinedload(User.role), joinedload(User.department)).where(func.lower(User.email) == otp_data.email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

    # 2. Find active and matching OTP
    # Fetch most recent OTP for the user that matches
    stmt = (
        select(UserOTP)
        .where(UserOTP.user_id == user.id)
        .where(UserOTP.otp_code == otp_data.otp_code)
        .order_by(UserOTP.created_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    db_otp = res.scalars().first()

    if not db_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    if db_otp.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has already been used"
        )

    # Make expires_at timezone aware for safe comparison
    expires_at = db_otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired (5-minute limit)"
        )

    # 3. Mark OTP as used (Single-use flag)
    db_otp.is_used = True
    await db.flush()

    # 4. Generate JWT Tokens
    role_id_str = str(user.role_id) if user.role_id else "0"
    access_token = create_access_token(subject=str(user.id), role_id=role_id_str)
    refresh_token = create_refresh_token(subject=str(user.id))

    # 5. Set Secure HTTP-Only Cookies
    is_secure = settings.ENVIRONMENT.lower() in ["production", "staging", "secure"]
    
    # Access Token Cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=is_secure,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    # Refresh Token Cookie (Valid for 7 days)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="none",
        max_age=7 * 24 * 60 * 60, # 7 days
        path="/"
    )

    return {
        "message": "Successfully authenticated",
        "user": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role_id": role_id_str,
            "role_name": user.role.name if user.role else None,
            "department": user.department.name if user.department else None
        }
    }


@router.post("/refresh", summary="Renovación Silenciosa del Access Token")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Silent Refresh: Reads the Refresh Token from the HTTP-Only cookie,
    validates it, issues a new Access Token and Refresh Token, and sets the cookies.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    try:
        payload = verify_refresh_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid payload sub")
    except ValueError as e:
        logger.warning(f"Invalid refresh token received: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Verify user in database
    stmt = select(User).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Generate new tokens
    role_id_str = str(user.role_id) if user.role_id else "0"
    new_access_token = create_access_token(subject=str(user.id), role_id=role_id_str)
    new_refresh_token = create_refresh_token(subject=str(user.id))

    # Set cookies
    is_secure = settings.ENVIRONMENT.lower() in ["production", "staging", "secure"]
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        secure=is_secure,
        samesite="none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )

    return {"message": "Token successfully refreshed"}


@router.post("/logout", summary="Cierre de Sesión")
async def logout(response: Response) -> Any:
    """
    Clears both secure HTTP-Only cookies.
    """
    is_secure = settings.ENVIRONMENT.lower() in ["production", "staging", "secure"]
    
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=is_secure,
        samesite="none",
        path="/"
    )
    
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=is_secure,
        samesite="none",
        path="/"
    )
    
    return {"message": "Successfully logged out"}

class VerifyEmailRequest(BaseModel):
    token: str

@router.post("/verify-email", summary="Verificar cuenta mediante enlace de correo")
async def verify_email_endpoint(
    request_data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    from app.core.security import verify_verification_token
    try:
        email = verify_verification_token(request_data.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    stmt = select(User).where(func.lower(User.email) == email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    await db.flush()
    return {"message": "Email successfully verified"}


class ChangePasswordRequest(BaseModel):
    new_password: str

@router.post("/change-password", summary="Cambio obligatorio de contraseña")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(User).where(User.id == current_user.id)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    from app.core.hashing import hash_password

    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")

    user.password_hash = hash_password(password_data.new_password)
    user.must_change_password = False
    await db.flush()

    return {"message": "Password changed successfully"}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

@router.post("/forgot-password", summary="Solicitar restablecimiento de contraseña")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(User).where(func.lower(User.email) == data.email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        # We return success anyway to prevent email enumeration
        return {"message": "If the email is registered, you will receive an OTP code to reset your password."}

    if not user.is_active:
        return {"message": "If the email is registered, you will receive an OTP code to reset your password."}

    # Generate random 6-digit numeric OTP
    otp = f"{random.randint(100000, 999999)}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Store OTP in DB
    db_otp = UserOTP(
        user_id=user.id,
        otp_code=otp,
        expires_at=expires_at,
        is_used=False
    )
    db.add(db_otp)
    await db.flush()

    # Send OTP
    from app.services.notification import send_reset_password_otp_email
    import asyncio
    asyncio.create_task(send_reset_password_otp_email(user.email, otp))

    return {"message": "If the email is registered, you will receive an OTP code to reset your password."}


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str
    new_password: str

@router.post("/reset-password", summary="Restablecer contraseña con OTP")
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(User).where(func.lower(User.email) == data.email.lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")

    # Find active and matching OTP
    stmt_otp = (
        select(UserOTP)
        .where(UserOTP.user_id == user.id)
        .where(UserOTP.otp_code == data.otp_code)
        .order_by(UserOTP.created_at.desc())
        .limit(1)
    )
    res_otp = await db.execute(stmt_otp)
    db_otp = res_otp.scalars().first()

    if not db_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

    if db_otp.is_used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has already been used")

    expires_at = db_otp.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired (5-minute limit)")

    from app.core.hashing import hash_password

    if len(data.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long")

    # Update password and mark OTP as used
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    db_otp.is_used = True
    await db.flush()

    return {"message": "Password has been successfully reset. You can now log in."}
