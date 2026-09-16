from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100, description="Full name of user")
    phone: Optional[str] = Field(None, max_length=20, description="User phone number")
    email: str = Field(..., max_length=100, description="User email address")


class UserProfileCreate(UserProfileBase):
    id: UUID = Field(..., description="User UUID matching auth service user ID")
    balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        description="Initial balance for user account"
    )


class UserProfileResponse(UserProfileBase):
    id: UUID
    balance: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserBalanceResponse(BaseModel):
    user_id: UUID
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class BalanceUpdateRequest(BaseModel):
    amount: Decimal = Field(
        ...,
        gt=Decimal("0.00"),
        description="Amount to deduct or refund (must be greater than 0)"
    )
    operation: Literal["deduct", "refund"] = Field(
        ...,
        description="Operation type: 'deduct' or 'refund'"
    )


class BalanceUpdateResponse(BaseModel):
    user_id: UUID
    old_balance: Decimal
    new_balance: Decimal

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    transaction_id: UUID = Field(..., description="Reference transaction UUID")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Transaction amount")
    type: str = Field(default="PAYMENT", max_length=20, description="Transaction type")


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    transaction_id: UUID
    description: Optional[str] = None
    amount: Decimal
    type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedTransactionsResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(from_attributes=True)
