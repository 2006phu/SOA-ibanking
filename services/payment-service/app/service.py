import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple, List

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logger import get_correlation_id
from app.models import Transaction
from app.rabbitmq import rabbitmq_client
from app.schemas import (
    PaymentInitiateResponse,
    PaymentConfirmResponse,
    PaymentVerifyOtpResponse,
)

logger = logging.getLogger(__name__)


async def call_service(method: str, url: str, **kwargs) -> Any:
    """Helper to perform HTTP requests to other microservices with correlation ID forwarding."""
    headers = kwargs.pop("headers", {}) or {}
    cid = get_correlation_id()
    if cid and "X-Correlation-ID" not in headers:
        headers["X-Correlation-ID"] = cid

    logger.info(f"Calling inter-service endpoint [{method}] {url}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        if response.content:
            return response.json()
        return None


class PaymentService:
    """Orchestrates payment operations, inter-service HTTP calls, and Saga transactions."""

    @staticmethod
    async def initiate_payment(
        db: AsyncSession,
        user_id: uuid.UUID,
        mssv: str,
        tuition_fee_id: uuid.UUID,
        idempotency_key: Optional[str] = None,
    ) -> Transaction:
        # 1. Idempotency Check
        if idempotency_key:
            stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
            result = await db.execute(stmt)
            existing_tx = result.scalar_one_or_none()
            if existing_tx:
                if existing_tx.user_id != user_id:
                    logger.warning(f"Idempotency key collision for user {user_id} on key {idempotency_key}")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Duplicate idempotency key registered under a different user",
                    )
                logger.info(f"Returning existing transaction {existing_tx.id} for idempotency key {idempotency_key}")
                return existing_tx

        # 2. Call Tuition Service: verify fee exists and is UNPAID
        tuition_url = f"{settings.TUITION_SERVICE_URL}/api/tuition/fee/{tuition_fee_id}"
        try:
            fee_data = await call_service("GET", tuition_url)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tuition fee not found")
            logger.error(f"Tuition service returned error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Tuition service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Cannot reach tuition service at {tuition_url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tuition service is currently unavailable",
            )

        fee_status = str(fee_data.get("status", "")).upper()
        if fee_status != "UNPAID":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tuition fee is already {fee_status.lower() or 'paid'}",
            )

        fee_mssv = str(fee_data.get("mssv", "")).strip()
        if fee_mssv and fee_mssv.lower() != mssv.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MSSV mismatch: fee belongs to student {fee_mssv}, requested for {mssv}",
            )

        try:
            amount = Decimal(str(fee_data.get("amount")))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid fee amount received")

        student_name = fee_data.get("student_name")

        # 3. Call User Service: check sufficient balance
        balance_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/balance"
        try:
            user_balance_data = await call_service("GET", balance_url)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            logger.error(f"User service returned error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"User service balance error: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Cannot reach user service at {balance_url}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service is currently unavailable",
            )

        try:
            current_balance = Decimal(str(user_balance_data.get("balance", 0)))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user balance received")

        # 4. Validate balance
        if current_balance < amount:
            logger.info(f"User {user_id} insufficient balance ({current_balance}) for amount ({amount})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Current balance is {current_balance}, required amount is {amount}",
            )

        # 5. Create Transaction with status PENDING
        tx = Transaction(
            user_id=user_id,
            tuition_fee_id=tuition_fee_id,
            mssv=mssv,
            student_name=student_name,
            amount=amount,
            status="PENDING",
            user_balance_before=current_balance,
            idempotency_key=idempotency_key,
            created_at=datetime.now(timezone.utc),
        )
        db.add(tx)
        await db.commit()
        await db.refresh(tx)
        logger.info(f"Created transaction {tx.id} with status PENDING for student {mssv}")
        return tx

    @staticmethod
    async def confirm_payment(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        user_id: uuid.UUID,
        email: Optional[str] = None,
    ) -> Transaction:
        # 1. Lock and verify transaction
        stmt = select(Transaction).where(Transaction.id == transaction_id).with_for_update()
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        if tx.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Transaction does not belong to the authenticated user",
            )

        if tx.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction cannot be confirmed. Current status is {tx.status}",
            )

        # 2. Obtain user email if not provided
        target_email = email
        if not target_email:
            user_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}"
            try:
                user_info = await call_service("GET", user_url)
                if isinstance(user_info, dict):
                    target_email = user_info.get("email")
            except Exception as e:
                logger.warning(f"Failed to fetch user email from {user_url}: {e}")

        if not target_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email is required for sending OTP but could not be resolved",
            )

        # 3. Call OTP Service: POST /api/otp/generate
        otp_url = f"{settings.OTP_SERVICE_URL}/api/otp/generate"
        otp_code = None
        try:
            otp_res = await call_service(
                "POST",
                otp_url,
                json={"transaction_id": str(tx.id), "email": target_email},
            )
            if isinstance(otp_res, dict):
                otp_code = otp_res.get("otp_code")
        except httpx.HTTPStatusError as e:
            logger.error(f"OTP generation failed: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OTP service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Cannot reach OTP service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OTP service is currently unavailable",
            )

        # 4. Update status to OTP_SENT
        tx.status = "OTP_SENT"
        await db.commit()
        await db.refresh(tx)
        logger.info(f"Transaction {tx.id} transitioned to OTP_SENT with OTP code: {otp_code}")
        return tx, otp_code

    @staticmethod
    async def verify_otp_and_pay(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        user_id: uuid.UUID,
        otp_code: str,
    ) -> Transaction:
        # 1. Lock and verify transaction
        stmt = select(Transaction).where(Transaction.id == transaction_id).with_for_update()
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        if tx.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Transaction does not belong to the authenticated user",
            )

        if tx.status != "OTP_SENT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transaction is not awaiting OTP verification. Current status: {tx.status}",
            )

        # 2. Call OTP Service: verify OTP
        otp_verify_url = f"{settings.OTP_SERVICE_URL}/api/otp/verify"
        try:
            verify_res = await call_service(
                "POST",
                otp_verify_url,
                json={"transaction_id": str(tx.id), "otp_code": otp_code},
            )
            # If verify endpoint returns a boolean or dict status
            if isinstance(verify_res, dict) and verify_res.get("valid") is False:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=verify_res.get("message", "Invalid or expired OTP"),
                )
        except httpx.HTTPStatusError as e:
            logger.warning(f"OTP verification failed with status {e.response.status_code}: {e.response.text}")
            if e.response.status_code in (400, 401):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired OTP code",
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OTP service error: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Cannot reach OTP service: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OTP service is currently unavailable",
            )

        # 3. CRITICAL SECTION (SAGA ORCHESTRATION)
        # Step a: Call User Service: PUT /api/users/{user_id}/balance (deduct)
        deduct_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/balance"
        balance_after: Optional[Decimal] = None

        try:
            deduct_res = await call_service(
                "PUT",
                deduct_url,
                json={"amount": float(tx.amount), "operation": "deduct"},
            )
            if isinstance(deduct_res, dict):
                raw_balance = deduct_res.get("balance") or deduct_res.get("new_balance")
                if raw_balance is not None:
                    balance_after = Decimal(str(raw_balance))
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to deduct balance for user {user_id}: {e.response.text}")
            tx.status = "FAILED"
            await db.commit()
            detail_msg = "Failed to deduct user balance"
            try:
                err_data = e.response.json()
                detail_msg = err_data.get("detail", detail_msg)
            except Exception:
                pass
            raise HTTPException(status_code=e.response.status_code, detail=detail_msg)
        except httpx.RequestError as e:
            logger.error(f"Cannot reach user service to deduct balance: {e}")
            tx.status = "FAILED"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service unavailable during balance deduction",
            )

        # Fallback balance_after calculation if not returned directly by user service
        if balance_after is None and tx.user_balance_before is not None:
            balance_after = tx.user_balance_before - tx.amount

        # Step b: Call Tuition Service: PUT /api/tuition/fee/{tuition_fee_id}/pay
        tuition_pay_url = f"{settings.TUITION_SERVICE_URL}/api/tuition/fee/{tx.tuition_fee_id}/pay"
        tuition_payment_succeeded = False
        tuition_error_status = status.HTTP_400_BAD_REQUEST
        tuition_error_msg = "Tuition payment failed"

        try:
            await call_service(
                "PUT",
                tuition_pay_url,
                json={"paid_by_user_id": str(user_id), "transaction_id": str(tx.id)},
            )
            tuition_payment_succeeded = True
        except httpx.HTTPStatusError as e:
            tuition_error_status = e.response.status_code
            try:
                err_data = e.response.json()
                tuition_error_msg = err_data.get("detail", e.response.text)
            except Exception:
                tuition_error_msg = e.response.text
            logger.error(f"Tuition payment call failed: {tuition_error_status} - {tuition_error_msg}")
        except httpx.RequestError as e:
            tuition_error_status = status.HTTP_503_SERVICE_UNAVAILABLE
            tuition_error_msg = f"Tuition service unavailable: {str(e)}"
            logger.error(f"Cannot reach tuition service during pay: {e}")

        # Step c: SAGA COMPENSATION if step b failed
        if not tuition_payment_succeeded:
            logger.warning(
                f"SAGA COMPENSATION TRIGGERED for tx {tx.id}: Refunding {tx.amount} to user {user_id}"
            )
            refund_success = False
            refund_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/balance"
            try:
                await call_service(
                    "PUT",
                    refund_url,
                    json={"amount": float(tx.amount), "operation": "refund"},
                )
                refund_success = True
                logger.info(f"Saga refund completed successfully for user {user_id}, amount: {tx.amount}")
            except Exception as comp_err:
                logger.critical(
                    f"CRITICAL: Saga compensation refund failed for user {user_id}, transaction {tx.id}! Error: {comp_err}"
                )

            tx.status = "FAILED"
            await db.commit()

            final_status = status.HTTP_409_CONFLICT if tuition_error_status == 409 else status.HTTP_400_BAD_REQUEST
            refund_note = "Balance has been refunded." if refund_success else "CRITICAL: Balance refund failed. Please contact support."
            raise HTTPException(
                status_code=final_status,
                detail=f"Tuition payment failed: {tuition_error_msg}. {refund_note}",
            )

        # 4. Tuition payment succeeded: Update transaction status
        completed_at = datetime.now(timezone.utc)
        tx.status = "SUCCESS"
        tx.user_balance_after = balance_after
        tx.completed_at = completed_at
        await db.commit()
        await db.refresh(tx)
        logger.info(f"Transaction {tx.id} marked as SUCCESS")

        # 5. Record transaction history: POST /api/users/{user_id}/transactions
        history_url = f"{settings.USER_SERVICE_URL}/api/users/{user_id}/transactions"
        try:
            await call_service(
                "POST",
                history_url,
                json={
                    "transaction_id": str(tx.id),
                    "amount": float(tx.amount),
                    "type": "PAYMENT",
                    "status": "SUCCESS",
                    "description": f"Tuition payment for MSSV {tx.mssv}",
                    "reference_id": str(tx.tuition_fee_id),
                },
            )
            logger.info(f"Recorded transaction history in User Service for tx {tx.id}")
        except Exception as hist_err:
            logger.warning(f"Failed to record transaction history for tx {tx.id}: {hist_err}")

        # 6. Retrieve email for RabbitMQ event
        user_email = None
        try:
            user_data = await call_service("GET", f"{settings.USER_SERVICE_URL}/api/users/{user_id}")
            if isinstance(user_data, dict):
                user_email = user_data.get("email")
        except Exception as email_err:
            logger.warning(f"Failed to fetch user email for RabbitMQ notification: {email_err}")

        # 7. Publish event to RabbitMQ queue 'payment_success'
        event_data = {
            "transaction_id": str(tx.id),
            "user_id": str(tx.user_id),
            "mssv": tx.mssv,
            "student_name": tx.student_name,
            "amount": float(tx.amount),
            "email": user_email,
            "completed_at": tx.completed_at.isoformat() if tx.completed_at else None,
        }
        try:
            await rabbitmq_client.publish_payment_success(event_data, settings.RABBITMQ_URL)
            logger.info(f"Published payment_success event to RabbitMQ for tx {tx.id}")
        except Exception as mq_err:
            logger.error(f"Failed to publish payment_success event for tx {tx.id}: {mq_err}")

        return tx

    @staticmethod
    async def get_transaction(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction:
        """Fetch transaction by ID."""
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        result = await db.execute(stmt)
        tx = result.scalar_one_or_none()
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return tx

    @staticmethod
    async def get_user_transactions(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        size: int = 10,
    ) -> Tuple[List[Transaction], int]:
        """Fetch paginated transactions for a user."""
        count_stmt = select(func.count()).select_from(Transaction).where(Transaction.user_id == user_id)
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        offset = (page - 1) * size
        list_stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        items_res = await db.execute(list_stmt)
        items = list(items_res.scalars().all())

        return items, total
