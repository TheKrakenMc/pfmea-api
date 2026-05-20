from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Optional

from app.core.db import get_db
from app.models.user import User
from app.core.security import create_access_token, limiter, settings
from app.api.deps import get_current_user, CurrentUser
from pydantic import BaseModel, EmailStr

router = APIRouter()


# ---------------------------------------------------------------------------
# Session verification
# ---------------------------------------------------------------------------

class UserRead(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_id: str
    is_active: bool


@router.get("/me", response_model=UserRead, summary="Obtener usuario actual")
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Return the current authenticated user's profile.
    Reads the JWT from the HttpOnly cookie via the get_current_user dependency.
    """
    stmt = select(User).where(User.id == int(current_user.id))
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
        role_id=current_user.role_id,
        is_active=user.is_active,
    )

class LoginRequest(BaseModel):
    email: EmailStr
    # Add password or other credentials if needed in the future

@router.post("/login", response_model=dict)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login endpoint with strict rate limiting.
    Authenticates user and sets HttpOnly cookie.
    """
    # 1. Fetch user by email
    stmt = select(User).where(User.email == login_data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or credentials"
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # 2. Create access token
    access_token = create_access_token(
        subject=str(user.id),
        role_id=str(user.role_id) if user.role_id else "0"
    )

    # 3. Set secure HttpOnly cookie
    is_secure = settings.ENVIRONMENT.lower() in ["production", "staging", "secure"]
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return {"message": "Successfully logged in"}

@router.post("/logout", response_model=dict)
async def logout(response: Response) -> Any:
    """Logout endpoint to clear the secure cookie."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.ENVIRONMENT.lower() in ["production", "staging", "secure"],
        samesite="lax",
    )
    return {"message": "Successfully logged out"}
