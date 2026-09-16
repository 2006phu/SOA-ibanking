import logging
import uuid
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TransactionHistory, UserProfile
from app.schemas import (
    BalanceUpdateRequest,
    BalanceUpdateResponse,
    PaginatedTransactionsResponse,
    TransactionCreate,
    TransactionResponse,
    UserBalanceResponse,
    UserProfileCreate,
)

logger = logging.getLogger("user-service.service")


class UserService:
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> UserProfile:
        """Fetch a user profile by user UUID."""
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"User profile not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile with ID '{user_id}' not found",
            )
        return user

    @staticmethod
    async def get_balance(db: AsyncSession, user_id: uuid.UUID) -> UserBalanceResponse:
        """Retrieve user current balance."""
        user = await UserService.get_user_by_id(db, user_id)
        return UserBalanceResponse(user_id=user.id, balance=user.balance)

    @staticmethod
    async def update_balance(
        db: AsyncSession, user_id: uuid.UUID, data: BalanceUpdateRequest
    ) -> BalanceUpdateResponse:
        """
        Update user balance safely using SELECT ... FOR UPDATE for concurrency safety.
        Serializes concurrent deductions and refunds.
        """
        stmt = select(UserProfile).where(UserProfile.id == user_id).with_for_update()
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Balance update failed: user not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found",
            )

        old_balance = user.balance

        if data.operation == "deduct":
            if user.balance < data.amount:
                logger.warning(
                    f"Insufficient balance for user {user_id}. "
                    f"Current: {user.balance}, Required: {data.amount}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Insufficient balance. "
                        f"Current balance: {user.balance}, requested: {data.amount}"
                    ),
                )
            user.balance = user.balance - data.amount
            logger.info(
                f"Balance deducted for user {user_id}: {data.amount}. "
                f"Old: {old_balance}, New: {user.balance}"
            )
        elif data.operation == "refund":
            user.balance = user.balance + data.amount
            logger.info(
                f"Balance refunded for user {user_id}: {data.amount}. "
                f"Old: {old_balance}, New: {user.balance}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation '{data.operation}'. Must be 'deduct' or 'refund'",
            )

        await db.commit()
        await db.refresh(user)

        return BalanceUpdateResponse(
            user_id=user.id,
            old_balance=old_balance,
            new_balance=user.balance,
        )

    @staticmethod
    async def create_user(db: AsyncSession, data: UserProfileCreate) -> UserProfile:
        """Create a new user profile when user registers via auth service."""
        # Check if ID already exists
        existing_id = await db.get(UserProfile, data.id)
        if existing_id:
            logger.warning(f"User ID conflict: {data.id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with ID '{data.id}' already exists",
            )

        # Check if email already exists
        email_stmt = select(UserProfile).where(UserProfile.email == data.email)
        email_result = await db.execute(email_stmt)
        if email_result.scalar_one_or_none():
            logger.warning(f"User email conflict: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{data.email}' already exists",
            )

        new_user = UserProfile(
            id=data.id,
            full_name=data.full_name,
            phone=data.phone,
            email=data.email,
            balance=data.balance,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"Created user profile for user {new_user.id} ({new_user.email})")
        return new_user

    @staticmethod
    async def get_transactions(
        db: AsyncSession, user_id: uuid.UUID, page: int = 1, size: int = 10
    ) -> PaginatedTransactionsResponse:
        """Retrieve paginated transactions for a user ordered by created_at DESC."""
        # Verify user exists
        await UserService.get_user_by_id(db, user_id)

        # Count total
        count_stmt = (
            select(func.count())
            .select_from(TransactionHistory)
            .where(TransactionHistory.user_id == user_id)
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Query items
        offset = (page - 1) * size
        items_stmt = (
            select(TransactionHistory)
            .where(TransactionHistory.user_id == user_id)
            .order_by(TransactionHistory.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items_result = await db.execute(items_stmt)
        items = list(items_result.scalars().all())

        return PaginatedTransactionsResponse(
            items=[TransactionResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    @staticmethod
    async def create_transaction(
        db: AsyncSession, user_id: uuid.UUID, data: TransactionCreate
    ) -> TransactionHistory:
        """Record a transaction in the user's transaction history."""
        # Verify user exists
        await UserService.get_user_by_id(db, user_id)

        transaction = TransactionHistory(
            user_id=user_id,
            transaction_id=data.transaction_id,
            description=data.description,
            amount=data.amount,
            type=data.type,
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        logger.info(
            f"Recorded transaction {transaction.id} for user {user_id} "
            f"(type={data.type}, amount={data.amount})"
        )
        return transaction
