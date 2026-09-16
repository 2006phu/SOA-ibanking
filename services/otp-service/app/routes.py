from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    OTPGenerateRequest,
    OTPGenerateResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
)
from app.service import otp_service

router = APIRouter(tags=["OTP"])


@router.post(
    "/api/otp/generate",
    response_model=OTPGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate OTP for a transaction",
)
@router.post(
    "/generate",
    response_model=OTPGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def generate_otp(
    request: OTPGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    if not request.email or not request.email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )
    return await otp_service.generate_otp(db=db, request=request)


@router.post(
    "/api/otp/verify",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP for a transaction",
)
@router.post(
    "/verify",
    response_model=OTPVerifyResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    if not request.otp_code or not request.otp_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP code is required",
        )
    return await otp_service.verify_otp(db=db, request=request)
