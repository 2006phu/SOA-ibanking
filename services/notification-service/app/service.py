import logging
from typing import Any
from app.email_sender import send_otp_email, send_payment_confirmation_email

logger = logging.getLogger("notification-service.service")


class NotificationService:
    """Service layer handling notification workflows."""

    @staticmethod
    async def process_otp_notification(email: str, code: str, transaction_id: str) -> bool:
        """Process and send an OTP notification."""
        return await send_otp_email(
            email=email,
            code=code,
            transaction_id=transaction_id
        )

    @staticmethod
    async def process_payment_confirmation(
        email: str,
        transaction_id: str,
        student_name: str,
        mssv: str,
        amount: Any,
        completed_at: str
    ) -> bool:
        """Process and send a payment confirmation receipt."""
        return await send_payment_confirmation_email(
            email=email,
            transaction_id=transaction_id,
            student_name=student_name,
            mssv=mssv,
            amount=amount,
            completed_at=completed_at
        )
