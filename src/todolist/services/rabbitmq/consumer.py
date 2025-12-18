import os
import logging
import json
import asyncio
import signal
from datetime import datetime, timezone

import aio_pika
from src.todolist.websocket.manager import ws_manager
from src.todolist.config import RABBIT_URL
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


EXCHANGE_NAME = "list_updates_sharded"
NUM_SHARDS = 4
SHARD_INDEX = 0
QUEUE_NAME = f"list_updates_shard_{SHARD_INDEX}"
PREFETCH_COUNT = 1

running = True

# Graceful shutdown
def handle_signal(signum, frame):
    global running
    logger.info(f"[worker] Received signal {signum}, shutting down...")
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# Shard routing key helper
def shard_routing_key(shard_idx: int) -> str:
    return f"shard.{shard_idx}"

# Process one message
async def process_message(body_bytes: bytes):
    """
    Deserialize message from RabbitMQ and broadcast via ws_manager.
    """
    try:
        msg = json.loads(body_bytes.decode())
        list_id = msg.get("list_id")
        if list_id is None:
            logger.info(f"[worker] Malformed message (missing list_id): {msg}")
            return

        # Broadcast using WebSocket manager
        try:
            await ws_manager.broadcast_task_event(list_id, msg)
            logger.info(f"[{datetime.now(timezone.utc).isoformat()}] Broadcasted event for list {list_id}")
        except Exception as e:
            logger.info("[worker] Failed to broadcast to Redis:", e)


    except Exception as e:
        logger.info("[worker] Error processing message:", e)


async def main():
    global running

    # Connect Redis via ws_manager's pubsub
    await ws_manager.pubsub.connect()

    # Connect to RabbitMQ
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBIT_URL)
            channel = await connection.channel()
            break
        except Exception as e:
            logger.info("[worker] RabbitMQ connection failed, retrying in 2s...", e)
            await asyncio.sleep(2)

    # Declare exchange and queue
    exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    routing_key = shard_routing_key(SHARD_INDEX)
    await queue.bind(exchange, routing_key)

    await channel.set_qos(prefetch_count=PREFETCH_COUNT)

    logger.info(f"[worker] Started. Serving shard {SHARD_INDEX} -> queue '{QUEUE_NAME}' bound to '{routing_key}'")

    # Message handler callback
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            if not running:
                break
            async with message.process(requeue=True):
                await process_message(message.body)

    # Close connections on shutdown
    await channel.close()
    await connection.close()
    logger.info("[worker] Stopped.")


if __name__ == "__main__":
    asyncio.run(main())
