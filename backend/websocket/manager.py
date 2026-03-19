from __future__ import annotations

import json
from typing import Dict, Set

from fastapi import WebSocket

from backend.game.registry import GameRegistry
from backend.websocket.events import (
    ClientToServerEvent,
    ServerToClientEvent,
    VotePayload,
    UseAbilityPayload,
)


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
            await ws.send_text(json.dumps(data))

    async def handle_client_message(
        self,
        game_id: str,
        websocket: WebSocket,
        raw_text: str,
    ) -> None:
        event = ClientToServerEvent.model_validate_json(raw_text)
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
        elif event.event == "vote":
            game = self.registry.get_or_create(game_id)
            payload = VotePayload.model_validate(event.payload)
            # voter_id는 프론트 계약에 없어서, 일단 sender로부터 추정(미포함 시 "unknown")
            voter_id = event.payload.get("sender", "unknown") if isinstance(event.payload, dict) else "unknown"
            game.submit_vote(voter_id=voter_id, target_id=payload.target)
            await self.broadcast(
                game_id,
                ServerToClientEvent(
                    event="vote_result",
                    payload={
                        "target": payload.target,
                        "votes": game.get_vote_snapshot(),
                        "executed": False,
                    },
                ),
            )
        elif event.event == "use_ability":
            game = self.registry.get_or_create(game_id)
            payload = UseAbilityPayload.model_validate(event.payload)
            agent_id = event.payload.get("sender", "unknown") if isinstance(event.payload, dict) else "unknown"
            game.submit_ability(agent_id=agent_id, ability=payload.ability, target_id=payload.target)
            await self.broadcast(
                game_id,
                ServerToClientEvent(
                    event="ability_result",
                    payload={
                        "type": payload.ability,
                        "success": True,
                        "detail": {"target": payload.target},
                    },
                ),
            )
