import asyncio
import json
import logging
import uuid
from typing import Any, Callable, Dict, Optional
import aio_pika

from app.config import settings
from app.email_sender import send_otp_email, send_payment_confirmation_email
from app.logging_config import correlation_id_ctx, set_correlation_id

logger = logging.getLogger("notification-service.consumer")


class RabbitMQConsumer:
    """RabbitMQ consumer listening on 'otp_email' and 'payment_success' queues."""

    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.is_connected: bool = False
        self.queues = ["otp_email", "payment_success"]
        self._stop_event = asyncio.Event()

    def get_status(self) -> Dict[str, Any]:
        """Return consumer status."""
        return {
            "status": "ok" if self.is_connected else "connecting",
            "queues": self.queues,
            "connected": self.is_connected
        }

    async def start(self):
        """Connect to RabbitMQ and start consuming from configured queues."""
        while not self._stop_event.is_set():
            try:
                masked_url = self._mask_url(settings.RABBITMQ_URL)
                logger.info(
                    f"Connecting to RabbitMQ at {masked_url}...",
                    extra={"url": masked_url}
                )

                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()
                await self.channel.set_qos(prefetch_count=10)

                # Declare durable queues
                otp_queue = await self.channel.declare_queue("otp_email", durable=True)
                payment_queue = await self.channel.declare_queue("payment_success", durable=True)

                # Bind consumers
                await otp_queue.consume(self._handle_otp_message)
                await payment_queue.consume(self._handle_payment_message)

                self.is_connected = True
                logger.info(
                    "RabbitMQ consumer successfully connected and listening on queues: 'otp_email', 'payment_success'",
                    extra={"queues": self.queues}
                )

                # Wait until stop is signaled
                await self._stop_event.wait()
                break

            except asyncio.CancelledError:
                logger.info("RabbitMQ consumer task cancelled")
                break
            except Exception as exc:
                self.is_connected = False
                logger.error(
                    f"RabbitMQ connection failed: {exc}. Retrying in 5 seconds...",
                    extra={"error": str(exc)},
                    exc_info=True
                )
                try:
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    break

    async def stop(self):
        """Stop consumer and release RabbitMQ connection resources."""
        self._stop_event.set()
        self.is_connected = False
        if self.channel and not self.channel.is_closed:
            try:
                await self.channel.close()
            except Exception as e:
                logger.warning(f"Error closing RabbitMQ channel: {e}")
        if self.connection and not self.connection.is_closed:
            try:
                await self.connection.close()
            except Exception as e:
                logger.warning(f"Error closing RabbitMQ connection: {e}")
        logger.info("RabbitMQ consumer stopped successfully")

    def _mask_url(self, url: str) -> str:
        try:
            if "@" in url:
                parts = url.split("@", 1)
                return "amqp://***:***@" + parts[1]
        except Exception:
            pass
        return "amqp://***"

    async def _handle_otp_message(self, message: aio_pika.abc.AbstractIncomingMessage):
        """Handler for 'otp_email' queue."""
        await self._process_message_with_retry(
            message=message,
            queue_name="otp_email",
            dispatcher=self._dispatch_otp
        )

    async def _handle_payment_message(self, message: aio_pika.abc.AbstractIncomingMessage):
        """Handler for 'payment_success' queue."""
        await self._process_message_with_retry(
            message=message,
            queue_name="payment_success",
            dispatcher=self._dispatch_payment_success
        )

    async def _process_message_with_retry(
        self,
        message: aio_pika.abc.AbstractIncomingMessage,
        queue_name: str,
        dispatcher: Callable[[Dict[str, Any]], Any]
    ):
        """Process incoming message with 3 retries and exponential backoff."""
        payload: Dict[str, Any] = {}
        raw_body = message.body.decode("utf-8", errors="replace")

        try:
            payload = json.loads(raw_body)
        except Exception as parse_err:
            logger.error(
                f"Failed to parse message body as JSON from '{queue_name}': {parse_err}",
                extra={"queue": queue_name, "raw_body": raw_body}
            )
            # Cannot parse -> reject without requeue
            await message.reject(requeue=False)
            return

        # Extract or generate correlation ID
        correlation_id = (
            message.correlation_id
            or (payload.get("correlation_id") if isinstance(payload, dict) else None)
            or (payload.get("correlationId") if isinstance(payload, dict) else None)
            or str(uuid.uuid4())
        )
        token = set_correlation_id(correlation_id)

        logger.info(
            f"Received message from queue '{queue_name}'",
            extra={
                "action": "MESSAGE_RECEIVED",
                "queue": queue_name,
                "correlation_id": correlation_id,
                "message_id": message.message_id or "",
                "payload": payload
            }
        )

        max_retries = 3
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                # Dispatch message to specific business logic
                await dispatcher(payload)

                # Acknowledge message upon successful processing
                await message.ack()
                logger.info(
                    f"Successfully processed and acknowledged message from '{queue_name}' on attempt {attempt}",
                    extra={
                        "action": "MESSAGE_ACKNOWLEDGED",
                        "queue": queue_name,
                        "correlation_id": correlation_id,
                        "attempt": attempt
                    }
                )
                correlation_id_ctx.reset(token)
                return

            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed for message from '{queue_name}': {exc}",
                    extra={
                        "action": "MESSAGE_RETRY",
                        "queue": queue_name,
                        "correlation_id": correlation_id,
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "error": str(exc)
                    }
                )

                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s...
                    backoff_delay = 2 ** (attempt - 1)
                    await asyncio.sleep(backoff_delay)

        # Retries exhausted -> Reject message without requeue to prevent poisoning queue
        logger.error(
            f"Message from queue '{queue_name}' failed after {max_retries} attempts. Rejecting message.",
            extra={
                "action": "MESSAGE_REJECTED",
                "queue": queue_name,
                "correlation_id": correlation_id,
                "max_retries": max_retries,
                "error": str(last_exception),
                "payload": payload
            },
            exc_info=True
        )

        try:
            await message.reject(requeue=False)
        except Exception as rej_exc:
            logger.error(f"Error rejecting message from '{queue_name}': {rej_exc}")

        correlation_id_ctx.reset(token)

    async def _dispatch_otp(self, payload: Dict[str, Any]):
        """Validate and dispatch OTP email message."""
        if not isinstance(payload, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(payload)}")

        email = payload.get("email")
        code = payload.get("code") or payload.get("otp_code")
        transaction_id = payload.get("transaction_id") or payload.get("transactionId") or ""

        if not email:
            raise ValueError(f"Missing 'email' in otp_email message: {payload}")
        if not code:
            raise ValueError(f"Missing 'code' in otp_email message: {payload}")

        await send_otp_email(
            email=str(email),
            code=str(code),
            transaction_id=str(transaction_id)
        )

    async def _dispatch_payment_success(self, payload: Dict[str, Any]):
        """Validate and dispatch Payment Success confirmation email."""
        if not isinstance(payload, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(payload)}")

        email = payload.get("email")
        transaction_id = payload.get("transaction_id") or payload.get("transactionId") or ""
        student_name = payload.get("student_name") or payload.get("studentName") or payload.get("full_name") or "Sinh viên"
        mssv = payload.get("mssv") or payload.get("student_id") or payload.get("studentId") or ""
        amount = payload.get("amount")
        completed_at = payload.get("completed_at") or payload.get("completedAt") or payload.get("timestamp") or ""

        if not email:
            raise ValueError(f"Missing 'email' in payment_success message: {payload}")
        if amount is None:
            raise ValueError(f"Missing 'amount' in payment_success message: {payload}")

        await send_payment_confirmation_email(
            email=str(email),
            transaction_id=str(transaction_id),
            student_name=str(student_name),
            mssv=str(mssv),
            amount=amount,
            completed_at=str(completed_at)
        )


consumer = RabbitMQConsumer()
