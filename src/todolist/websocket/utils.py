# src/todolist/websocket/utils.py
import logging
from jose import jwt, JWTError
from jose.exceptions import JWKError
from fastapi import HTTPException, status
from src.todolist.config import TODOLIST_JWT_SECRET, TODOLIST_JWT_ALG

log = logging.getLogger(__name__)

def decode_jwt_token(token: str) -> dict:
    try:
        # 🔍 ENABLE DEBUG (TEMPORARILY)
        print(f"DEBUG: Decoding token: {token[:20]}...{token[-10:]}")
        print(f"DEBUG: Token length: {len(token)}")
        print(f"DEBUG: Using Secret: {TODOLIST_JWT_SECRET[:10]}***")
        print(f"DEBUG: Using Alg: {TODOLIST_JWT_ALG}")
        
        # 🛑 FIX: Ensure algorithms is a LIST
        algo_list = [TODOLIST_JWT_ALG] if isinstance(TODOLIST_JWT_ALG, str) else TODOLIST_JWT_ALG
        
        print(f"DEBUG: algo_list = {algo_list}")
        
        payload = jwt.decode(
            token, 
            TODOLIST_JWT_SECRET, 
            algorithms=algo_list
        )
        
        print(f"DEBUG: ✅ Token decoded successfully! User ID: {payload.get('sub')}")
        return payload
        
    except (JWTError, JWKError) as e:
        print(f"DEBUG: ❌ JWT Error: {type(e).__name__}: {str(e)}")
        log.error(f"❌ WebSocket JWT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid or expired token: {str(e)}",
        )