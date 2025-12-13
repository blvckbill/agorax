from fastapi import APIRouter, WebSocket, status
from sqlalchemy.orm import Session
from src.todolist.database.core import SessionLocal
from src.todolist.websocket.manager import ws_manager
from src.todolist.auth.service import get
from src.todolist.auth.models import TodolistUser
from .utils import decode_jwt_token

import logging
log = logging.getLogger(__name__)

ws_router = APIRouter()

async def get_current_user_ws(websocket: WebSocket) -> TodolistUser | None:
    """
    Extracts token and authenticates user.
    """
    print(f"DEBUG: WebSocket connection attempt")
    
    # 1. Try Query Param (Preferred for WS)
    token = websocket.query_params.get("token")
    print(f"DEBUG: Token from query params: {token[:20] if token else 'None'}...")
    
    # 2. Try Header (Fallback)
    if not token:
        auth_header = websocket.headers.get("Authorization")
        print(f"DEBUG: Auth header: {auth_header}")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    
    if not token:
        print("DEBUG: ❌ No token found!")
        return None
    
    session: Session = SessionLocal()
    try:
        # Validate Token
        print("DEBUG: Attempting to decode token...")
        payload = decode_jwt_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            print("DEBUG: ❌ No user_id in payload!")
            return None
        
        print(f"DEBUG: Getting user with ID: {user_id}")
        user = get(db_session=session, user_id=int(user_id))
        
        if user:
            print(f"DEBUG: ✅ User found: {user.email}")
        else:
            print(f"DEBUG: ❌ User not found in database!")
        
        return user
        
    except Exception as e:
        print(f"DEBUG: ❌ Exception in get_current_user_ws: {type(e).__name__}: {str(e)}")
        return None
    finally:
        session.close()


@ws_router.websocket("/ws/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: int):
    print(f"DEBUG: WebSocket endpoint called for list {list_id}")
    
    # 1. Authenticate (Handshake Phase)
    user = await get_current_user_ws(websocket)
    
    if not user:
        print(f"DEBUG: ❌ Authentication failed, closing connection with 1008")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION) 
        return
    
    print(f"DEBUG: ✅ User authenticated, accepting connection")
    
    # 2. Accept (Connection Phase)
    await websocket.accept()
    
    print(f"DEBUG: Connection accepted, connecting to manager")
    
    # 3. Connect to Manager
    await ws_manager.connect_user(list_id, websocket, user)
    
    try:
        while True:
            # Keep the connection open
            message = await websocket.receive_text()
            print(f"DEBUG: Received message: {message}")
    except Exception as e:
        print(f"DEBUG: WebSocket exception: {type(e).__name__}: {str(e)}")
    finally:
        print(f"DEBUG: Disconnecting user from manager")
        await ws_manager.disconnect_user(list_id, websocket)
