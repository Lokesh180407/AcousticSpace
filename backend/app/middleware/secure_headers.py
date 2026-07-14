from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """Add a minimal secure headers set.

    Note: Rate limiting is architecture-ready but not enforced by default.
    """

    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response


def add_secure_headers_middleware(app: FastAPI) -> None:
    app.add_middleware(SecureHeadersMiddleware)

