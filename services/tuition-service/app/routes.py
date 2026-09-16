import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    HealthResponse,
    PayTuitionRequest,
    PayTuitionResponse,
    StudentCreate,
    StudentResponse,
    StudentTuitionResponse,
    TuitionFeeCreate,
    TuitionFeeDetailResponse,
)
from app.service import (
    create_student,
    create_tuition_fee,
    get_student_tuition_by_mssv,
    get_tuition_fee_by_id,
    pay_tuition_fee,
    seed_initial_data,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify service and database status."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="tuition-service",
        database=db_status,
    )


# CRITICAL: Define /fee routes BEFORE /{mssv} so "fee" is not parsed as a student MSSV
@router.get(
    "/api/tuition/fee/{tuition_id}",
    response_model=TuitionFeeDetailResponse,
    tags=["Tuition"],
    summary="Get specific tuition fee detail",
)
async def get_fee_detail(
    tuition_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information for a specific tuition fee by UUID."""
    return await get_tuition_fee_by_id(db=db, tuition_id=tuition_id)


@router.put(
    "/api/tuition/fee/{tuition_id}/pay",
    response_model=PayTuitionResponse,
    tags=["Tuition"],
    summary="Mark tuition fee as paid",
)
async def pay_fee(
    tuition_id: UUID,
    payload: PayTuitionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Internal endpoint to mark tuition fee as paid.
    Uses SELECT ... FOR UPDATE for strict concurrency control.
    """
    return await pay_tuition_fee(
        db=db, tuition_id=tuition_id, payload=payload
    )


@router.get(
    "/api/tuition/{mssv}",
    response_model=StudentTuitionResponse,
    tags=["Tuition"],
    summary="Look up student and unpaid tuition fees by MSSV",
)
async def get_tuition_by_mssv(
    mssv: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Look up student by student ID (MSSV) and return student information
    along with their UNPAID tuition fees only.
    """
    return await get_student_tuition_by_mssv(db=db, mssv=mssv)


# Administrative & Helper Endpoints
@router.post(
    "/api/tuition/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin"],
    summary="Create student record",
)
async def add_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new student in the system."""
    return await create_student(db=db, data=data)


@router.post(
    "/api/tuition/fees",
    response_model=TuitionFeeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin"],
    summary="Create tuition fee",
)
async def add_tuition_fee(
    data: TuitionFeeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tuition fee for an existing student."""
    return await create_tuition_fee(db=db, data=data)


@router.post(
    "/api/tuition/seed",
    tags=["Admin"],
    summary="Seed sample tuition data",
)
async def trigger_seed(
    db: AsyncSession = Depends(get_db),
):
    """Manually seed sample data if empty."""
    await seed_initial_data(db=db)
    return {"message": "Sample tuition data seeded"}
