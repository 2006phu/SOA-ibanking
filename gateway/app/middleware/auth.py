import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

# Paths that bypass authentication checks
PUBLIC_EXACT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "",
    "/",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts Bearer token from Authorization header.
    2. Decodes JWT using PyJWT with SECRET_KEY.
    3. Extracts user_id, username, email from payload.
    4. Attaches extracted user context to request.state.
    5. Allows downstream handlers to inject X-User-ID, X-User-Email.
    Skips auth for: POST /api/auth/login, GET /health, GET /docs, GET /openapi.json, OPTIONS preflight.
    """

    async def dispatch(self, request: Request, call_next):
        # 1. Skip CORS preflight OPTIONS requests
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # 2. Skip public endpoints
        path = request.url.path.rstrip("/")
        if not path:
            path = "/"

        if path in PUBLIC_EXACT_PATHS:
            return await call_next(request)

        # Skip login and register endpoints
        if path == "/api/auth/login" and request.method.upper() == "POST":
            return await call_next(request)

        if path == "/api/auth/register" and request.method.upper() == "POST":
            return await call_next(request)

        correlation_id = getattr(request.state, "correlation_id", "")
        error_headers = {"X-Correlation-ID": correlation_id} if correlation_id else {}

        # 3. Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required. Missing Authorization header."},
                headers=error_headers,
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication scheme. Bearer token required."},
                headers=error_headers,
            )

        token = parts[1]

        # 4. Decode and verify JWT
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token has expired. Please log in again."},
                headers=error_headers,
            )
        except jwt.InvalidTokenError as exc:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid token: {str(exc)}."},
                headers=error_headers,
            )

        # 5. Extract user identifiers
        user_id = payload.get("user_id") or payload.get("sub") or payload.get("id")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token payload: missing user identifier."},
                headers=error_headers,
            )

        # 6. Store user details on request.state
        request.state.user = payload
        request.state.user_id = str(user_id)
        request.state.user_email = payload.get("email")
        request.state.user_username = payload.get("username")
        request.state.jwt_token = token

        return await call_next(request)


async def get_current_user(request: Request) -> dict:
    """Dependency to retrieve the authenticated user payload."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_current_user_id(request: Request) -> str:
    """Dependency to retrieve the authenticated user ID."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return str(user_id)
