from fastapi import APIRouter, Request
from app.config import settings
from app.proxy import proxy_request

router = APIRouter()


@router.get("/me")
async def get_my_info(request: Request):
    """
    Get current user profile from User Service.
    Converts 'me' to the actual user_id from the verified JWT before forwarding.
    """
    user_id = getattr(request.state, "user_id", None)
    target_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}"
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.get("/me/balance")
async def get_my_balance(request: Request):
    """
    Get current user account balance from User Service.
    Converts 'me' to the actual user_id from the verified JWT before forwarding.
    """
    user_id = getattr(request.state, "user_id", None)
    target_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/balance"
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.get("/me/transactions")
async def get_my_transactions(request: Request):
    """
    Get current user transaction history from User Service.
    Converts 'me' to the actual user_id from the verified JWT before forwarding.
    """
    user_id = getattr(request.state, "user_id", None)
    target_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/transactions"
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.get("/{user_id}")
async def get_user_by_id(user_id: str, request: Request):
    """
    Get user profile by user_id from User Service.
    """
    target_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}"
    current_user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=current_user_id,
    )


@router.get("/{user_id}/balance")
async def get_user_balance(user_id: str, request: Request):
    """
    Get user account balance by user_id from User Service.
    """
    target_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/balance"
    current_user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=current_user_id,
    )


@router.get("/{user_id}/transactions")
async def get_user_transactions(user_id: str, request: Request):
    """
    Get user transactions by user_id from User Service.
    """
    target_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/transactions"
    current_user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=current_user_id,
    )
