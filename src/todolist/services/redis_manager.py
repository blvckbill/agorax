import asyncio
import json
import redis.asyncio as redis

from fastapi import WebSocket
from typing import Callable, Dict, Set, List


class RedisPubSubManager:
    """Redis Pub/Sub manager for multiple rooms/users."""

    def __init__(self, host="localhost", port=6379):
        self.redis_host = host
        self.redis_port = port
        self.redis: redis.Redis | None = None
        self.room_listeners: Dict[str, asyncio.Task] = {}  # room_id -> listener task
        self.room_callbacks: Dict[str, Set[Callable]] = {}  # room_id -> set of async callbacks


    async def _get_redis_connection(self) -> redis.Redis:
        """Establish or return the Redis connection."""
        if not self.redis:
            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
        return self.redis


    async def connect(self):
        """Ensure Redis connection is established."""
        await self._get_redis_connection()

    async def publish(self, room_id: str, message: str):
        """Publish a message to a specific room/channel."""
        if not self.redis:
            await self.connect()
        await self.redis.publish(room_id, message)


    async def subscribe(self, room_id: str, callback: Callable[[str], None]):
        """
        Subscribe a callback to a room.
        Starts a listener task if not already running.
        """
        if room_id not in self.room_callbacks:
            self.room_callbacks[room_id] = set()
        self.room_callbacks[room_id].add(callback)

        # Start listener task for room if it doesn't exist
        if room_id not in self.room_listeners:
            self.room_listeners[room_id] = asyncio.create_task(self._room_listener(room_id))


    async def unsubscribe(self, room_id: str, callback: Callable[[str], None]):
        """Unsubscribe a callback from a room. Stop listener if no callbacks remain."""
        if room_id in self.room_callbacks:
            self.room_callbacks[room_id].discard(callback)
            if not self.room_callbacks[room_id]:
                # Cancel listener task
                task = self.room_listeners.pop(room_id, None)
                if task:
                    task.cancel()
                self.room_callbacks.pop(room_id, None)


    async def _room_listener(self, room_id: str):
        """Internal async listener task for a room."""
        redis_conn = await self._get_redis_connection()
        pubsub = redis_conn.pubsub()
        await pubsub.subscribe(room_id)

        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    # Send message to all callbacks registered for this room
                    for callback in self.room_callbacks.get(room_id, set()):
                        await callback(message['data'])
        except asyncio.CancelledError:
            # Gracefully unsubscribe when task is canceled
            await pubsub.unsubscribe(room_id)
        finally:
            await pubsub.close()
