from fastapi import APIRouter, WebSocket, status
from sqlalchemy.orm import Session
from src.todolist.database.core import SessionLocal
from src.todolist.websocket.manager import ws_manager
from src.todolist.auth.service import get
from src.todolist.auth.models import TodolistUser
from .utils import decode_jwt_token_ws

ws_router = APIRouter()


async def get_current_user_ws(websocket: WebSocket) -> TodolistUser | None:
    """
    Authenticate user via JWT token from query params or Authorization header.
    Returns TodolistUser or None if authentication fails.
    """
    # Extract token from query parameters
    token = websocket.query_params.get("token")

    # If not in query params, check Authorization header
    if not token:
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]  # Strip "Bearer "

    if not token:
        return None

    session: Session = SessionLocal()
    try:
        payload = await decode_jwt_token_ws(websocket)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = get(db_session=session, user_id=user_id)
        return user
    finally:
        session.close()


@ws_router.websocket("/ws/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: int):
    """
    WebSocket endpoint for a specific ToDo list.
    Handles JWT authentication via query params or Authorization header.
    """
    # Authenticate user
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept the WebSocket connection
    await websocket.accept()

    # Connect the user to WebSocket manager
    await ws_manager.connect_user(list_id, websocket, user)

    try:
        while True:
            # Keep connection alive and optionally handle incoming messages
            message = await websocket.receive_text()
            # Optional: process the message here
    except Exception:
        pass
    finally:
        # Cleanly disconnect the user
        await ws_manager.disconnect_user(list_id, websocket)
