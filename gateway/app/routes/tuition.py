from fastapi import APIRouter, Request
from app.config import settings
from app.proxy import proxy_request

router = APIRouter()


@router.get("/{mssv}")
async def get_tuition_by_mssv(mssv: str, request: Request):
    """
    Forward student tuition lookup to Tuition Service.
    """
    target_url = f"{settings.TUITION_SERVICE_URL}/api/tuition/{mssv}"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.get("")
async def list_tuition(request: Request):
    """
    Forward tuition list / query to Tuition Service.
    """
    target_url = f"{settings.TUITION_SERVICE_URL}/api/tuition"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.post("")
async def create_or_update_tuition(request: Request):
    """
    Forward tuition creation / payment status update to Tuition Service.
    """
    target_url = f"{settings.TUITION_SERVICE_URL}/api/tuition"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="POST",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )
