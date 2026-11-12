"""WebSocket：私信实时推送。

路径固定为 /ws（不挂在业务前缀下），前端通过 /ws?token=... 连接。
"""
import asyncio
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .security import parse_token

router = APIRouter()


class ConnectionManager:
    """按用户维护 WebSocket 连接，支持同一用户多标签页。"""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[user_id].discard(websocket)

    async def send_to(self, user_id: int, payload: dict) -> None:
        for websocket in list(self._connections.get(user_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:  # noqa: BLE001 - 单个连接失败不影响其他
                await self.disconnect(user_id, websocket)

    def online(self, user_id: int) -> bool:
        return bool(self._connections.get(user_id))


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = ""):
    payload = parse_token(token)
    if not payload:
        await websocket.close(code=4401)
        return

    user_id = int(payload["uid"])
    await manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "ready", "user_id": user_id})
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)
    except Exception:  # noqa: BLE001
        await manager.disconnect(user_id, websocket)
