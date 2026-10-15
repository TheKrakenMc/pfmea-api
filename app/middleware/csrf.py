"""Origin checks protect browser credential requests; session-bound CSRF checks live in auth dependencies."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import get_settings


class OriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin and origin not in get_settings().get_allowed_origins:
                return JSONResponse(
                    {"detail": "Untrusted request origin"}, status_code=403
                )
            if request.headers.get("sec-fetch-site") == "cross-site" and not origin:
                return JSONResponse(
                    {"detail": "Request origin required"}, status_code=403
                )
        return await call_next(request)
