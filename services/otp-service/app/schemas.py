import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class OTPGenerateRequest(BaseModel):
    transaction_id: uuid.UUID = Field(..., description="Unique transaction ID")
    email: str = Field(..., max_length=100, description="Recipient email address")


class OTPGenerateResponse(BaseModel):
    otp_id: uuid.UUID = Field(..., description="Unique OTP record ID")
    transaction_id: uuid.UUID = Field(..., description="Transaction ID")
    expires_at: datetime = Field(..., description="OTP expiration timestamp")
    otp_code: Optional[str] = Field(None, description="Generated OTP code for debug/demo")

    model_config = ConfigDict(from_attributes=True)


class OTPVerifyRequest(BaseModel):
    transaction_id: uuid.UUID = Field(..., description="Unique transaction ID")
    otp_code: str = Field(..., description="6-digit OTP code")


class OTPVerifyResponse(BaseModel):
    valid: bool = Field(..., description="Whether the OTP is valid")
    transaction_id: uuid.UUID = Field(..., description="Transaction ID")

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    rabbitmq: str
