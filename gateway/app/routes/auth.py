from fastapi import APIRouter, Request
from app.config import settings
from app.proxy import proxy_request

router = APIRouter()


@router.post("/login")
async def login(request: Request):
    """
    Forward login request to Auth Service.
    No authentication required.
    """
    target_url = f"{settings.AUTH_SERVICE_URL}/api/auth/login"
    return await proxy_request(method="POST", target_url=target_url, request=request)


@router.post("/register")
async def register(request: Request):
    """
    Forward registration request to Auth Service.
    No authentication required.
    """
    target_url = f"{settings.AUTH_SERVICE_URL}/api/auth/register"
    return await proxy_request(method="POST", target_url=target_url, request=request)


@router.get("/me")
async def get_current_user_auth(request: Request):
    """
    Forward authenticated user verification request to Auth Service.
    Auth required, token is passed along with headers.
    """
    target_url = f"{settings.AUTH_SERVICE_URL}/api/auth/me"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )
