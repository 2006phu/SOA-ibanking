import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentInitiateRequest(BaseModel):
    mssv: str = Field(..., min_length=1, max_length=20, description="Student ID")
    tuition_fee_id: uuid.UUID = Field(..., description="ID of tuition fee to be paid")


class PaymentInitiateResponse(BaseModel):
    transaction_id: uuid.UUID
    mssv: str
    student_name: Optional[str] = None
    amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


class PaymentConfirmRequest(BaseModel):
    email: Optional[str] = Field(None, description="Optional recipient email for OTP")


class PaymentConfirmResponse(BaseModel):
    transaction_id: uuid.UUID
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class PaymentVerifyOtpRequest(BaseModel):
    otp_code: str = Field(..., min_length=1, max_length=10, description="One-Time Password")


class PaymentVerifyOtpResponse(BaseModel):
    transaction_id: uuid.UUID
    status: str
    amount: Decimal
    balance_after: Optional[Decimal] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tuition_fee_id: uuid.UUID
    mssv: str
    student_name: Optional[str] = None
    amount: Decimal
    status: str
    user_balance_before: Optional[Decimal] = None
    user_balance_after: Optional[Decimal] = None
    idempotency_key: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedTransactionsResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    service: str = "payment-service"
