import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    BalanceUpdateRequest,
    BalanceUpdateResponse,
    PaginatedTransactionsResponse,
    TransactionCreate,
    TransactionResponse,
    UserBalanceResponse,
    UserProfileCreate,
    UserProfileResponse,
)
from app.service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post(
    "",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user profile",
    description="Internal endpoint called when user registers in auth service",
)
@router.post(
    "/",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_user_profile(
    payload: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.create_user(db=db, data=payload)


@router.get(
    "/{user_id}",
    response_model=UserProfileResponse,
    summary="Get user profile",
    description="Get profile details of a user by UUID",
)
async def get_user_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_user_by_id(db=db, user_id=user_id)


@router.get(
    "/{user_id}/balance",
    response_model=UserBalanceResponse,
    summary="Get user balance",
    description="Get current balance for a user",
)
async def get_user_balance(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_balance(db=db, user_id=user_id)


@router.put(
    "/{user_id}/balance",
    response_model=BalanceUpdateResponse,
    summary="Update user balance",
    description="Deduct or refund user balance using SELECT FOR UPDATE for concurrency safety",
)
async def update_user_balance(
    user_id: uuid.UUID,
    payload: BalanceUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.update_balance(db=db, user_id=user_id, data=payload)


@router.get(
    "/{user_id}/transactions",
    response_model=PaginatedTransactionsResponse,
    summary="Get user transactions",
    description="Get paginated transaction history for a user, ordered by creation date DESC",
)
async def get_user_transactions(
    user_id: uuid.UUID,
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    return await UserService.get_transactions(db=db, user_id=user_id, page=page, size=size)


@router.post(
    "/{user_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record user transaction",
    description="Internal endpoint to record a transaction in user history",
)
async def create_user_transaction(
    user_id: uuid.UUID,
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
):
    return await UserService.create_transaction(db=db, user_id=user_id, data=payload)
