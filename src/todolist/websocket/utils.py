import logging
from fastapi import WebSocket, status, HTTPException
from jose import jwt, JWTError
from jose.exceptions import JWKError
from src.todolist.config import TODOLIST_JWT_SECRET, TODOLIST_JWT_ALG

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def decode_jwt_token_ws(websocket: WebSocket) -> dict:
    """
    Decode JWT token for a WebSocket connection.
    Token can come from:
      - query parameters (preferred)
      - Authorization header ("Bearer <token>")
    """
    token: str | None = websocket.query_params.get("token")

    if not token:
        auth_header = websocket.headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]  # strip "Bearer "

    if not token:
        log.exception("No JWT token provided in query params or headers")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "Could not validate credentials"}],
        )

    try:
        payload = jwt.decode(token, TODOLIST_JWT_SECRET, algorithms=TODOLIST_JWT_ALG)
        return payload
    except (JWTError, JWKError):
        log.exception("JWT token invalid or expired")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=[{"msg": "Could not validate credentials"}],
        )

