import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Student, TuitionFee
from app.schemas import (
    PayTuitionRequest,
    PayTuitionResponse,
    StudentCreate,
    StudentResponse,
    StudentTuitionResponse,
    TuitionFeeCreate,
    TuitionFeeDetailResponse,
    TuitionFeeItemResponse,
)

logger = logging.getLogger(__name__)


async def get_student_tuition_by_mssv(
    db: AsyncSession, mssv: str
) -> StudentTuitionResponse:
    """
    Look up student by MSSV and return their profile along with all UNPAID tuition fees.
    Raises 404 if student is not found.
    """
    stmt = select(Student).where(Student.mssv == mssv)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()

    if not student:
        logger.warning(f"Student with MSSV '{mssv}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Student with MSSV '{mssv}' not found",
        )

    # Filter only UNPAID tuition fees
    fee_stmt = (
        select(TuitionFee)
        .where(TuitionFee.mssv == mssv, TuitionFee.status == "UNPAID")
        .order_by(TuitionFee.created_at.desc())
    )
    fee_result = await db.execute(fee_stmt)
    unpaid_fees = fee_result.scalars().all()

    return StudentTuitionResponse(
        mssv=student.mssv,
        student_name=student.full_name,
        program=student.program,
        tuition_fees=[
            TuitionFeeItemResponse(
                id=fee.id,
                semester=fee.semester,
                amount=fee.amount,
                status=fee.status,
                paid_at=fee.paid_at,
            )
            for fee in unpaid_fees
        ],
    )


async def get_tuition_fee_by_id(
    db: AsyncSession, tuition_id: UUID
) -> TuitionFeeDetailResponse:
    """
    Get detailed information for a specific tuition fee.
    Raises 404 if tuition fee is not found.
    """
    stmt = (
        select(TuitionFee)
        .options(selectinload(TuitionFee.student))
        .where(TuitionFee.id == tuition_id)
    )
    result = await db.execute(stmt)
    fee = result.scalar_one_or_none()

    if not fee:
        logger.warning(f"Tuition fee with ID '{tuition_id}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Tuition fee with ID '{tuition_id}' not found",
        )

    student_name = fee.student.full_name if fee.student else ""

    return TuitionFeeDetailResponse(
        id=fee.id,
        mssv=fee.mssv,
        student_name=student_name,
        semester=fee.semester,
        amount=fee.amount,
        status=fee.status,
        paid_by_user_id=fee.paid_by_user_id,
        paid_at=fee.paid_at,
    )


async def pay_tuition_fee(
    db: AsyncSession, tuition_id: UUID, payload: PayTuitionRequest
) -> PayTuitionResponse:
    """
    Mark a tuition fee as PAID using SELECT ... FOR UPDATE for concurrency safety.
    Raises 404 if fee not found.
    Raises 409 if fee is already paid.
    """
    result = await db.execute(
        select(TuitionFee).where(TuitionFee.id == tuition_id).with_for_update()
    )
    fee = result.scalar_one_or_none()

    if not fee:
        logger.warning(f"Tuition fee with ID '{tuition_id}' not found for payment")
        raise HTTPException(
            status_code=404,
            detail=f"Tuition fee with ID '{tuition_id}' not found",
        )

    if fee.status == "PAID":
        logger.warning(
            f"Tuition fee with ID '{tuition_id}' has already been paid"
        )
        raise HTTPException(
            status_code=409,
            detail="Tuition fee already paid",
        )

    now = datetime.now(timezone.utc)
    fee.status = "PAID"
    fee.paid_by_user_id = payload.paid_by_user_id
    fee.paid_by_transaction_id = payload.transaction_id
    fee.paid_at = now
    fee.updated_at = now

    await db.flush()

    logger.info(
        f"Tuition fee '{tuition_id}' successfully marked as PAID by user '{payload.paid_by_user_id}' with tx '{payload.transaction_id}'"
    )

    return PayTuitionResponse(
        id=fee.id,
        status=fee.status,
        paid_at=fee.paid_at,
    )


async def create_student(
    db: AsyncSession, data: StudentCreate
) -> StudentResponse:
    """Create a new student record."""
    stmt = select(Student).where(Student.mssv == data.mssv)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Student with MSSV '{data.mssv}' already exists",
        )

    student = Student(
        mssv=data.mssv,
        full_name=data.full_name,
        program=data.program,
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return StudentResponse(
        id=student.id,
        mssv=student.mssv,
        full_name=student.full_name,
        program=student.program,
        created_at=student.created_at,
    )


async def create_tuition_fee(
    db: AsyncSession, data: TuitionFeeCreate
) -> TuitionFeeDetailResponse:
    """Create a new tuition fee for a student."""
    stmt = select(Student).where(Student.mssv == data.mssv)
    student = (await db.execute(stmt)).scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with MSSV '{data.mssv}' not found",
        )

    fee = TuitionFee(
        mssv=data.mssv,
        semester=data.semester,
        amount=data.amount,
        status="UNPAID",
    )
    db.add(fee)
    await db.flush()
    await db.refresh(fee)

    return TuitionFeeDetailResponse(
        id=fee.id,
        mssv=fee.mssv,
        student_name=student.full_name,
        semester=fee.semester,
        amount=fee.amount,
        status=fee.status,
        paid_by_user_id=fee.paid_by_user_id,
        paid_at=fee.paid_at,
    )


async def seed_initial_data(db: AsyncSession) -> None:
    """Seed sample students and tuition fees if database is empty."""
    count_stmt = select(func.count()).select_from(Student)
    count = (await db.execute(count_stmt)).scalar_one()

    if count > 0:
        return

    logger.info("Seeding initial student and tuition fee data...")

    students_data = [
        {
            "mssv": "52100888",
            "full_name": "Nguyễn Văn An",
            "program": "Công nghệ thông tin",
            "fees": [
                {
                    "semester": "HK1 2026-2027",
                    "amount": Decimal("12500000.00"),
                    "status": "UNPAID",
                },
                {
                    "semester": "HK2 2025-2026",
                    "amount": Decimal("11000000.00"),
                    "status": "PAID",
                    "paid_at": datetime.now(timezone.utc),
                },
            ],
        },
        {
            "mssv": "52100999",
            "full_name": "Trần Thị Bình",
            "program": "Kỹ thuật phần mềm",
            "fees": [
                {
                    "semester": "HK1 2026-2027",
                    "amount": Decimal("13200000.00"),
                    "status": "UNPAID",
                }
            ],
        },
        {
            "mssv": "52100777",
            "full_name": "Lê Hoàng Cường",
            "program": "Khoa học máy tính",
            "fees": [
                {
                    "semester": "HK1 2026-2027",
                    "amount": Decimal("10800000.00"),
                    "status": "UNPAID",
                }
            ],
        },
    ]

    for s_info in students_data:
        student = Student(
            mssv=s_info["mssv"],
            full_name=s_info["full_name"],
            program=s_info["program"],
        )
        db.add(student)
        await db.flush()

        for f_info in s_info["fees"]:
            fee = TuitionFee(
                mssv=student.mssv,
                semester=f_info["semester"],
                amount=f_info["amount"],
                status=f_info["status"],
                paid_at=f_info.get("paid_at"),
            )
            db.add(fee)

    await db.flush()
    logger.info("Sample tuition data seeded successfully.")
