from __future__ import annotations

from datetime import datetime
import json
from typing import Dict, Set

from fastapi import WebSocket

from backend.game.registry import GameRegistry
from backend.models.chat import ChatMessage
from backend.websocket.events import ClientToServerEvent, ServerToClientEvent


class ConnectionManager:
    def __init__(self, registry: GameRegistry) -> None:
        self.registry = registry
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
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                # 끊긴 소켓은 다음 disconnect에서 정리됨
                continue

    async def handle_client_message(
        self,
        game_id: str,
        websocket: WebSocket,
        raw_text: str,
    ) -> None:
        try:
            event = ClientToServerEvent.model_validate_json(raw_text)
        except Exception as e:
            await self.broadcast(
                game_id,
                ServerToClientEvent(
                    event="chat_broadcast",
                    payload={
                        "sender": "system",
                        "content": f"invalid_event: {e}",
                        "channel": "system",
                        "timestamp": datetime.utcnow().isoformat(),
                        "is_ai": False,
                    },
                ),
            )
            return

        try:
            if event.event == "chat_message":
                game = self.registry.get_or_create(game_id)
                payload = event.payload
                # GameState에 채팅 히스토리 저장 (후속: RAG/멀티턴에 활용)
                game.state.chat_history.append(
                    ChatMessage(
                        id=f"chat_{len(game.state.chat_history)+1}",
                        sender=payload.get("sender", "unknown"),
                        content=payload.get("content", ""),
                        channel="global",
                        timestamp=datetime.utcnow(),
                        is_ai=False,
                    )
                )
                await self.broadcast(
                    game_id,
                    ServerToClientEvent(
                        event="chat_broadcast",
                        payload={
                            "sender": payload.get("sender", "unknown"),
                            "content": payload.get("content", ""),
                            "channel": "global",
                            "timestamp": datetime.utcnow().isoformat(),
                            "is_ai": False,
                        },
                    ),
                )
            elif event.event == "vote":
                game = self.registry.get_or_create(game_id)
                payload = event.payload if isinstance(event.payload, dict) else {}
                target = payload.get("target")
                if not target:
                    return
                voter_id = payload.get("sender") or payload.get("voter") or "unknown"
                game.submit_vote(voter_id=str(voter_id), target_id=str(target))
                await self.broadcast(
                    game_id,
                    ServerToClientEvent(
                        event="vote_result",
                        payload={
                            "target": target,
                            "votes": game.get_vote_snapshot(),
                            "executed": False,
                        },
                    ),
                )
            elif event.event == "use_ability":
                game = self.registry.get_or_create(game_id)
                payload = event.payload if isinstance(event.payload, dict) else {}
                target = payload.get("target")
                ability = payload.get("ability")
                if not target or not ability:
                    return
                agent_id = payload.get("sender") or payload.get("agent_id") or "unknown"
                game.submit_ability(agent_id=str(agent_id), ability=str(ability), target_id=str(target))
                await self.broadcast(
                    game_id,
                    ServerToClientEvent(
                        event="ability_result",
                        payload={
                            "type": ability,
                            "success": True,
                            "detail": {"target": target},
                        },
                    ),
                )
            else:
                return
        except Exception as e:
            await self.broadcast(
                game_id,
                ServerToClientEvent(
                    event="chat_broadcast",
                    payload={
                        "sender": "system",
                        "content": f"handler_error: {e}",
                        "channel": "system",
                        "timestamp": datetime.utcnow().isoformat(),
                        "is_ai": False,
                    },
                ),
            )
            return
