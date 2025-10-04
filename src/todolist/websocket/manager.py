import asyncio
import json
import redis.asyncio as redis

from fastapi import WebSocket
from typing import Callable, Dict, Set, List

from src.todolist.services.redis_manager import RedisPubSubManager


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