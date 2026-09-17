import json
import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone

import aio_pika
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import OTPCode
from app.schemas import OTPGenerateRequest, OTPVerifyRequest

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.channel: aio_pika.abc.AbstractRobustChannel | None = None

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            # Ensure queue exists and is durable
            await self.channel.declare_queue("otp_email", durable=True)
            logger.info("Connected to RabbitMQ and declared 'otp_email' queue.")
        except Exception as e:
            logger.warning(f"Failed to connect to RabbitMQ at {settings.RABBITMQ_URL}: {e}")

    async def close(self) -> None:
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.warning(f"Error while closing RabbitMQ connection: {e}")

    def is_connected(self) -> bool:
        return (
            self.connection is not None
            and not self.connection.is_closed
            and self.channel is not None
            and not self.channel.is_closed
        )

    async def publish_otp(self, email: str, code: str, transaction_id: str) -> None:
        payload = {
            "email": email,
            "code": code,
            "transaction_id": str(transaction_id),
        }
        message_body = json.dumps(payload).encode("utf-8")

        if not self.is_connected():
            logger.info("RabbitMQ not connected, attempting to reconnect...")
            try:
                await self.connect()
            except Exception as conn_err:
                logger.error(f"Cannot connect to RabbitMQ to publish OTP: {conn_err}")
                return

        if self.is_connected() and self.channel:
            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            # Default exchange '' routes directly to queue with routing_key
            await self.channel.default_exchange.publish(
                message,
                routing_key="otp_email",
            )
            logger.info(
                f"Published OTP event to RabbitMQ queue 'otp_email' for transaction: {transaction_id}"
            )
        else:
            logger.error(
                f"Failed to publish OTP: RabbitMQ channel unavailable. Payload: {payload}"
            )


rabbitmq_client = RabbitMQClient()


class OTPService:
    @staticmethod
    def generate_random_code(length: int) -> str:
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    async def generate_otp(db: AsyncSession, request: OTPGenerateRequest) -> dict:
        # Check if OTP already exists for this transaction_id with row lock
        stmt = (
            select(OTPCode)
            .where(OTPCode.transaction_id == request.transaction_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        existing_otp = result.scalar_one_or_none()

        # Invalidate old OTP if it already exists
        if existing_otp:
            logger.info(
                f"Existing OTP found for transaction {request.transaction_id}. Invalidating old record."
            )
            await db.delete(existing_otp)
            await db.flush()

        code = OTPService.generate_random_code(settings.OTP_LENGTH)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.OTP_EXPIRATION_MINUTES)

        new_otp = OTPCode(
            id=uuid.uuid4(),
            transaction_id=request.transaction_id,
            code=code,
            email=request.email.strip(),
            is_used=False,
            expires_at=expires_at,
            created_at=now,
        )

        db.add(new_otp)
        await db.commit()
        await db.refresh(new_otp)

        logger.info(
            f"==================== [OTP CODE]: {code} for txn: {request.transaction_id} ===================="
        )

        # Publish message to RabbitMQ queue 'otp_email'
        try:
            await rabbitmq_client.publish_otp(
                email=new_otp.email,
                code=new_otp.code,
                transaction_id=str(new_otp.transaction_id),
            )
        except Exception as pub_err:
            logger.error(f"Error publishing OTP to RabbitMQ: {pub_err}", exc_info=True)

        return {
            "otp_id": new_otp.id,
            "transaction_id": new_otp.transaction_id,
            "expires_at": new_otp.expires_at,
            "otp_code": code,
        }

    @staticmethod
    async def verify_otp(db: AsyncSession, request: OTPVerifyRequest) -> dict:
        # Find OTP by transaction_id using SELECT ... FOR UPDATE
        stmt = (
            select(OTPCode)
            .where(OTPCode.transaction_id == request.transaction_id)
            .with_for_update()
        )
        result = await db.execute(stmt)
        otp = result.scalar_one_or_none()

        # 1. OTP exists -> 404 if not
        if not otp:
            logger.warning(f"OTP verification failed: transaction {request.transaction_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTP not found",
            )

        # 2. OTP is not used (is_used == False) -> 400 "OTP already used"
        if otp.is_used:
            logger.warning(f"OTP verification failed: transaction {request.transaction_id} already used")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP already used",
            )

        # 3. OTP is not expired (expires_at > now) -> 400 "OTP expired"
        now = datetime.now(timezone.utc)
        expires_at = otp.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            logger.warning(f"OTP verification failed: transaction {request.transaction_id} expired")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired",
            )

        # 4. Code matches -> 401 "Invalid OTP code"
        if otp.code != request.otp_code.strip():
            logger.warning(f"OTP verification failed: transaction {request.transaction_id} code mismatch")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP code",
            )

        # If all valid: mark is_used = True, commit
        otp.is_used = True
        await db.commit()
        await db.refresh(otp)

        logger.info(f"OTP verified successfully for transaction {request.transaction_id}")
        return {
            "valid": True,
            "transaction_id": otp.transaction_id,
        }


otp_service = OTPService()
