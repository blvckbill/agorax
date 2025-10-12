# src/todolist/messaging/rabbitmq_aio.py
import json
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import aio_pika

RABBIT_URL = "amqp://guest:guest@localhost:5672/"
EXCHANGE_NAME = "list_updates_sharded"
NUM_SHARDS = 4


class AsyncRabbitPublisher:
    """
    Async RabbitMQ publisher using aio_pika.
    - Designed for FastAPI async environment.
    - Call connect() at startup (lifespan) and close() at shutdown.
    """

    def __init__(self, rabbit_url: str = RABBIT_URL, exchange_name: str = EXCHANGE_NAME, num_shards: int = NUM_SHARDS):
        self.rabbit_url = rabbit_url
        self.exchange_name = exchange_name
        self.num_shards = num_shards

        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        """Establish connection, channel, and exchange."""
        self.connection = await aio_pika.connect_robust(self.rabbit_url)
        self.channel = await self.connection.channel()
        # Optional QoS: one message at a time
        await self.channel.set_qos(prefetch_count=1)
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

    async def close(self):
        """Close channel and connection."""
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    def shard_for_list(self, list_id: int) -> int:
        """Deterministic shard computation for a list_id."""
        h = int(hashlib.sha256(str(list_id).encode()).hexdigest(), 16)
        return h % self.num_shards

    def _routing_key_for_list(self, list_id: int) -> str:
        shard = self.shard_for_list(list_id)
        return f"shard.{shard}"

    async def publish_sharded_event(self, message: Dict[str, Any], list_id: int):
        """Publish message to the correct shard asynchronously."""
        if not self.exchange:
            raise RuntimeError("RabbitMQ exchange not connected. Call connect() first.")

        routing_key = self._routing_key_for_list(list_id)
        body = json.dumps(message, default=str).encode()

        await self.exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

rabbit_publisher = AsyncRabbitPublisher()
