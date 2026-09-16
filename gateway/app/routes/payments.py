from fastapi import APIRouter, Request
from app.config import settings
from app.proxy import proxy_request

router = APIRouter()


@router.post("/initiate")
async def initiate_payment(request: Request):
    """
    Forward payment initiation request to Payment Service.
    Injects X-User-ID and X-User-Email.
    """
    target_url = f"{settings.PAYMENT_SERVICE_URL}/api/payments/initiate"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="POST",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.post("/{txn_id}/confirm")
async def confirm_payment(txn_id: str, request: Request):
    """
    Forward payment confirmation request to Payment Service.
    Triggers OTP generation.
    Injects X-User-ID.
    """
    target_url = f"{settings.PAYMENT_SERVICE_URL}/api/payments/{txn_id}/confirm"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="POST",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.post("/{txn_id}/verify-otp")
async def verify_payment_otp(txn_id: str, request: Request):
    """
    Forward OTP verification request to Payment Service to complete tuition transaction.
    Injects X-User-ID.
    """
    target_url = f"{settings.PAYMENT_SERVICE_URL}/api/payments/{txn_id}/verify-otp"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="POST",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.get("/{txn_id}")
async def get_payment_details(txn_id: str, request: Request):
    """
    Forward payment transaction details query to Payment Service.
    """
    target_url = f"{settings.PAYMENT_SERVICE_URL}/api/payments/{txn_id}"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )


@router.get("")
async def list_payments(request: Request):
    """
    Forward payment list query to Payment Service.
    """
    target_url = f"{settings.PAYMENT_SERVICE_URL}/api/payments"
    user_id = getattr(request.state, "user_id", None)
    return await proxy_request(
        method="GET",
        target_url=target_url,
        request=request,
        user_id=user_id,
    )
