from typing import Any, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    queues: List[str] = ["otp_email", "payment_success"]


class OTPEmailPayload(BaseModel):
    email: str = Field(..., description="Recipient email address")
    code: str = Field(..., description="OTP verification code")
    transaction_id: str = Field(..., description="Transaction reference ID")

    model_config = {
        "extra": "ignore"
    }


class PaymentSuccessPayload(BaseModel):
    email: str = Field(..., description="Recipient email address")
    transaction_id: str = Field(..., description="Transaction reference ID")
    student_name: str = Field(..., description="Full student name")
    mssv: str = Field(..., description="Student ID number")
    amount: Any = Field(..., description="Payment amount in VND")
    completed_at: str = Field(..., description="Completion timestamp")

    model_config = {
        "extra": "ignore"
    }
