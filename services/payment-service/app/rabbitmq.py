import json
import logging
from typing import Optional
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ client using aio-pika for publishing events."""

    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.url: Optional[str] = None

    async def connect(self, rabbitmq_url: str) -> None:
        """Establish connection to RabbitMQ and declare the payment_success queue."""
        self.url = rabbitmq_url
        try:
            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            # Declare payment_success queue as durable
            await self.channel.declare_queue("payment_success", durable=True)
            logger.info("Connected to RabbitMQ and declared 'payment_success' queue successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}. Will attempt to reconnect upon publishing.")

    async def close(self) -> None:
        """Gracefully close channel and connection."""
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.warning(f"Error closing RabbitMQ connection: {e}")

    async def publish_payment_success(self, message_data: dict, rabbitmq_url: Optional[str] = None) -> None:
        """Publish payment success event to 'payment_success' queue."""
        url_to_use = rabbitmq_url or self.url
        try:
            if not self.connection or self.connection.is_closed or not self.channel or self.channel.is_closed:
                if url_to_use:
                    await self.connect(url_to_use)

            if not self.channel or self.channel.is_closed:
                raise RuntimeError("RabbitMQ channel is not available")

            body = json.dumps(message_data, default=str).encode("utf-8")
            message = aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            await self.channel.default_exchange.publish(
                message,
                routing_key="payment_success"
            )
            logger.info(f"Published payment_success event for transaction {message_data.get('transaction_id')}")
        except Exception as e:
            logger.error(f"Error publishing payment_success event to RabbitMQ: {e}")
            # Try once more with fresh connection if url is present
            if url_to_use:
                try:
                    logger.info("Retrying RabbitMQ publication with new connection...")
                    fresh_conn = await aio_pika.connect_robust(url_to_use)
                    fresh_channel = await fresh_conn.channel()
                    await fresh_channel.declare_queue("payment_success", durable=True)
                    body = json.dumps(message_data, default=str).encode("utf-8")
                    message = aio_pika.Message(
                        body=body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        content_type="application/json",
                    )
                    await fresh_channel.default_exchange.publish(
                        message,
                        routing_key="payment_success"
                    )
                    await fresh_channel.close()
                    await fresh_conn.close()
                    logger.info(f"Successfully published payment_success event on retry for transaction {message_data.get('transaction_id')}")
                    return
                except Exception as retry_e:
                    logger.error(f"Retry publication also failed: {retry_e}")
                    raise retry_e
            raise e


rabbitmq_client = RabbitMQClient()
