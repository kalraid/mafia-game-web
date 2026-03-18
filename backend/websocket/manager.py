from __future__ import annotations

import json
from typing import Dict, Set

from fastapi import WebSocket

from backend.websocket.events import ClientToServerEvent, ServerToClientEvent


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(game_id, set()).add(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket) -> None:
        if game_id in self._connections:
            self._connections[game_id].discard(websocket)
            if not self._connections[game_id]:
                del self._connections[game_id]

    async def broadcast(self, game_id: str, message: ServerToClientEvent) -> None:
        if game_id not in self._connections:
            return
        data = message.model_dump()
        for ws in list(self._connections[game_id]):
            await ws.send_text(json.dumps(data))

    async def handle_client_message(
        self,
        game_id: str,
        websocket: WebSocket,
        raw_text: str,
    ) -> None:
        event = ClientToServerEvent.model_validate_json(raw_text)
        # Phase 3에서는 단순 echo 형태로 chat_message만 브로드캐스트
        if event.event == "chat_message":
            payload = event.payload
            await self.broadcast(
                game_id,
                ServerToClientEvent(
                    event="chat_broadcast",
                    payload={
                        "sender": payload.get("sender", "unknown"),
                        "content": payload.get("content", ""),
                        "channel": "global",
                        "timestamp": None,
                        "is_ai": False,
                    },
                ),
            )
