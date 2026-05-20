from typing import List
from fastapi import Request, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_access_token
from app.core.db import get_db
from app.models.user import User


class CurrentUser(BaseModel):
    id: str
    role_id: str


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> CurrentUser:
    """
    Extract and validate JWT from the HttpOnly cookie.
    Assumes the cookie name is 'access_token'.
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
            
        # Verify user in database and check if active
        stmt = select(User).where(User.id == int(user_id))
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
            
        return CurrentUser(id=str(user.id), role_id=str(user.role_id) if user.role_id else "0")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


class RoleChecker:
    """
    Factory pattern for dependency injection to verify user roles.
    Example: dependencies=[Depends(RoleChecker(['PFMEA Owner', 'Administrator']))]
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
        
    async def __call__(self, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CurrentUser:
        """
        Execute role verification. Requires the current user.
        In a real application, you might map the role_id to the actual role name from DB.
        For now, we assume the allowed_roles check matches the logic required.
        """
        # If roles are checked by IDs, compare strings directly.
        # If allowed_roles are names, we would fetch role name using db.
        if str(user.role_id) not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return user
