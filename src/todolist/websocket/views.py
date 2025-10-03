from fastapi import APIRouter, WebSocket, Depends
from .manager import ws_manager

ws_router = APIRouter()

@ws_router.websocket("/ws/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: int):
    """Handle WebSocket connections for a specific ToDoList."""
    await ws_manager.connect_user(list_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        pass
    finally:
        await ws_manager.disconnect_user(list_id, websocket)