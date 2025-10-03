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

class WebSocketManager:
    """Manages WebSocket connections for ToDoList rooms (list_id)."""

    def __init__(self):
        self.rooms: Dict[int, List[WebSocket]] = {}
        self.redis_callbacks: Dict[int, Callable[[str], None]] = {}
        self.pubsub = RedisPubSubManager()

    async def connect_user(self, list_id: int, websocket: WebSocket):
        """Add user WebSocket to a ToDoList room."""
        await websocket.accept()

        if list_id not in self.rooms:
            self.rooms[list_id] = []
            cb = self._redis_callback(list_id)
            self.redis_callbacks[list_id] = cb
            # Subscribe to Redis updates for this list
            await self.pubsub.subscribe(f"todolist_{list_id}", cb)

        self.rooms[list_id].append(websocket)

    async def disconnect_user(self, list_id: int, websocket: WebSocket):
        """Remove user from ToDoList room."""
        self.rooms[list_id].remove(websocket)
        if not self.rooms[list_id]:
            cb = self.redis_callbacks.pop(list_id, None)
            if cb:
                await self.pubsub.unsubscribe(f"todolist_{list_id}", cb)
            del self.rooms[list_id]

    async def broadcast_task_event(self, list_id: int, event: dict):
        """
        Publish a task event to Redis (all connected users will see it).
        Example event: {"action": "task_added", "task": {...}}
        """
        await self.pubsub.publish(f"todolist_{list_id}", json.dumps(event))

    def _redis_callback(self, list_id: int):
        """Callback to send Redis updates to all clients in a ToDoList room."""

        async def callback(message: str):
            data = json.loads(message)
            if list_id in self.rooms:
                for socket in list(self.rooms[list_id]):
                    try:
                        await socket.send_json(data)
                    except Exception:
                        self.rooms[list_id].remove(socket)

        return callback

ws_manager = WebSocketManager()