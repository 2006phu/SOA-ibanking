import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="User's username")
    password: str = Field(..., min_length=1, max_length=128, description="User's password")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name")
    email: EmailStr = Field(..., max_length=100, description="Unique email address")
    phone: str | None = Field(default=None, max_length=20, description="Phone number")
    balance: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Initial balance")


class SeedUserRequest(BaseModel):
    id: str | None = Field(default=None, description="Optional fixed UUID for seeding")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    balance: float = Field(default=0.00)


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    phone: str | None = None
    email: str
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class VerifyResponse(BaseModel):
    user_id: str
    username: str
    email: str


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "auth-service"
