"""Sessions are checked against the database on every authenticated request."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from app.models.auth_session import AuthSession
from app.core.security import create_access_token, create_refresh_token, settings


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


async def issue_session(db, user, response, session=None):
    if session is None:
        session = AuthSession(
            id=secrets.token_urlsafe(32),
            user_id=user.id,
            csrf_token=secrets.token_urlsafe(32),
            refresh_hash="",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            revoked=False,
        )
        db.add(session)
    refresh = create_refresh_token(user.id, session_id=session.id)
    session.refresh_hash = digest(refresh)
    access = create_access_token(user.id, user.role_id or 0, session_id=session.id)
    secure = settings.ENVIRONMENT.lower() in {"production", "staging", "secure"}
    same = "none" if secure else "lax"
    for name, value, age in [
        ("access_token", access, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        ("refresh_token", refresh, 7 * 24 * 60 * 60),
        ("csrf_token", session.csrf_token, 7 * 24 * 60 * 60),
    ]:
        response.set_cookie(
            name,
            value,
            httponly=name != "csrf_token",
            secure=secure,
            samesite=same,
            max_age=age,
            path="/",
        )
    await db.flush()
    return session


async def revoke_user_sessions(db, user_id):
    await db.execute(
        update(AuthSession).where(AuthSession.user_id == user_id).values(revoked=True)
    )
