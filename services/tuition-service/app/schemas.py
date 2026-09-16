from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TuitionFeeItemResponse(BaseModel):
    id: UUID
    semester: str
    amount: Decimal = Field(..., gt=0, description="Tuition fee amount")
    status: str
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentTuitionResponse(BaseModel):
    mssv: str
    student_name: str
    program: Optional[str] = None
    tuition_fees: List[TuitionFeeItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TuitionFeeDetailResponse(BaseModel):
    id: UUID
    mssv: str
    student_name: str
    semester: str
    amount: Decimal = Field(..., gt=0, description="Tuition fee amount")
    status: str
    paid_by_user_id: Optional[UUID] = None
    paid_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PayTuitionRequest(BaseModel):
    paid_by_user_id: UUID
    transaction_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PayTuitionResponse(BaseModel):
    id: UUID
    status: str = "PAID"
    paid_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentCreate(BaseModel):
    mssv: str = Field(..., min_length=1, max_length=20)
    full_name: str = Field(..., min_length=1, max_length=100)
    program: Optional[str] = Field(None, max_length=200)

    model_config = ConfigDict(from_attributes=True)


class StudentResponse(BaseModel):
    id: UUID
    mssv: str
    full_name: str
    program: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TuitionFeeCreate(BaseModel):
    mssv: str = Field(..., min_length=1, max_length=20)
    semester: str = Field(..., min_length=1, max_length=20)
    amount: Decimal = Field(..., gt=0)

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "tuition-service"
    database: str = "connected"

    model_config = ConfigDict(from_attributes=True)
