import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    PaymentVerifyOtpRequest,
    PaymentVerifyOtpResponse,
    TransactionResponse,
    PaginatedTransactionsResponse,
)
from app.service import PaymentService

router = APIRouter(prefix="/api/payments", tags=["Payments"])


def get_current_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> uuid.UUID:
    """Extract and validate X-User-ID header injected by API Gateway."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-ID header is required",
        )
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-ID format. Must be a valid UUID",
        )


@router.post(
    "/initiate",
    response_model=PaymentInitiateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate a payment transaction",
)
async def initiate_payment(
    request: PaymentInitiateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    """Initiate payment for a tuition fee after checking fee status and user balance."""
    tx = await PaymentService.initiate_payment(
        db=db,
        user_id=user_id,
        mssv=request.mssv,
        tuition_fee_id=request.tuition_fee_id,
        idempotency_key=idempotency_key,
    )
    return PaymentInitiateResponse(
        transaction_id=tx.id,
        mssv=tx.mssv,
        student_name=tx.student_name,
        amount=tx.amount,
        status=tx.status,
    )


@router.post(
    "/{transaction_id}/confirm",
    response_model=PaymentConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm payment initiation and trigger OTP generation",
)
async def confirm_payment(
    transaction_id: uuid.UUID,
    request: Optional[PaymentConfirmRequest] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Confirm payment transaction, request OTP from OTP service, and update status to OTP_SENT."""
    email = request.email if request else None
    tx, otp_code = await PaymentService.confirm_payment(
        db=db,
        transaction_id=transaction_id,
        user_id=user_id,
        email=email,
    )
    return PaymentConfirmResponse(
        transaction_id=tx.id,
        status=tx.status,
        message="OTP has been sent to your email",
        otp_code=otp_code,
    )


@router.post(
    "/{transaction_id}/verify-otp",
    response_model=PaymentVerifyOtpResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and execute payment Saga orchestration",
)
async def verify_otp_and_pay(
    transaction_id: uuid.UUID,
    request: PaymentVerifyOtpRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Verify OTP, deduct balance, mark tuition fee paid with compensation on failure, and publish event."""
    tx = await PaymentService.verify_otp_and_pay(
        db=db,
        transaction_id=transaction_id,
        user_id=user_id,
        otp_code=request.otp_code,
    )
    return PaymentVerifyOtpResponse(
        transaction_id=tx.id,
        status=tx.status,
        amount=tx.amount,
        balance_after=tx.user_balance_after,
        completed_at=tx.completed_at,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full transaction details",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full details of a specific payment transaction."""
    tx = await PaymentService.get_transaction(db=db, transaction_id=transaction_id)
    return TransactionResponse.model_validate(tx)


@router.get(
    "/user/{user_id}",
    response_model=PaginatedTransactionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List all payment transactions for a user",
)
async def get_user_transactions(
    user_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number starting from 1"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated transactions for the specified user."""
    items, total = await PaymentService.get_user_transactions(
        db=db,
        user_id=user_id,
        page=page,
        size=size,
    )
    return PaginatedTransactionsResponse(
        items=[TransactionResponse.model_validate(tx) for tx in items],
        total=total,
        page=page,
        size=size,
    )
