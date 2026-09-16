from fastapi import APIRouter
from app.consumer import consumer
from app.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    tags=["Health"]
)
async def health_check():
    """Health check endpoint returning service status and monitored queues."""
    return HealthResponse(
        status="ok",
        queues=["otp_email", "payment_success"]
    )


@router.get(
    "/",
    summary="Root service info",
    tags=["Info"]
)
async def root():
    """Root info endpoint."""
    return {
        "service": "notification-service",
        "description": "iBanking Tuition Payment System - Notification Service",
        "status": "running",
        "port": 8006,
        "queues": ["otp_email", "payment_success"],
        "consumer": consumer.get_status()
    }
