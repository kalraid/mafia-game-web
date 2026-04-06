from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from typing import Dict, Optional, Set

from fastapi import WebSocket

from backend.game.registry import GameRegistry
from backend.models.chat import ChatMessage
from backend.models.game import Role, Team
from backend.websocket.events import ClientToServerEvent, ServerToClientEvent


class ConnectionManager:
    def __init__(self, registry: GameRegistry) -> None:
        self.registry = registry
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._ws_player_ids: Dict[str, Dict[WebSocket, Optional[str]]] = {}

    async def connect(self, game_id: str, websocket: WebSocket, player_id: str | None = None) -> None:
        await websocket.accept()
        self._connections.setdefault(game_id, set()).add(websocket)
        self._ws_player_ids.setdefault(game_id, {})[websocket] = player_id

    def disconnect(self, game_id: str, websocket: WebSocket) -> None:
        if game_id in self._connections:
            self._connections[game_id].discard(websocket)
            if not self._connections[game_id]:
                del self._connections[game_id]
        if game_id in self._ws_player_ids:
            self._ws_player_ids[game_id].pop(websocket, None)
            if not self._ws_player_ids[game_id]:
                del self._ws_player_ids[game_id]

    def _is_allowed_for_channel(self, game_id: str, websocket: WebSocket, channel: str) -> bool:
        if channel not in {"mafia_secret", "spy_listen"}:
            return True

        player_id = self._ws_player_ids.get(game_id, {}).get(websocket)
        if not player_id:
            return False

        game = self.registry.get(game_id)
        if game is None:
            return False
        player = next((p for p in game.state.players if p.id == player_id), None)
        if player is None:
            return False

        if channel == "mafia_secret":
            return player.team == Team.MAFIA
        # spy_listen: spy + mafia만 허용
        return player.team == Team.MAFIA or player.role == Role.SPY

    async def broadcast(self, game_id: str, message: ServerToClientEvent) -> None:
        if game_id not in self._connections:
            return
        data = message.model_dump()
        channel = ""
        if message.event == "chat_broadcast":
            payload_channel = message.payload.get("channel")
            if isinstance(payload_channel, str):
                channel = payload_channel
        for ws in list(self._connections[game_id]):
            if channel and not self._is_allowed_for_channel(game_id, ws, channel):
                continue
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
                game = self.registry.get(game_id)
                if game is None:
                    return
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
                game = self.registry.get(game_id)
                if game is None:
                    return
                payload = event.payload if isinstance(event.payload, dict) else {}
                target = payload.get("target")
                if not target:
                    return
                voter_id = payload.get("sender") or payload.get("voter") or "unknown"
                game.submit_vote(voter_id=str(voter_id), target_id=str(target))
                snap = game.get_vote_snapshot()
                tally = Counter(str(t) for t in snap.values() if t)
                await self.broadcast(
                    game_id,
                    ServerToClientEvent(
                        event="vote_result",
                        payload={
                            "target": target,
                            "votes": snap,
                            "votes_received": dict(tally),
                            "executed": False,
                        },
                    ),
                )
            elif event.event == "use_ability":
                game = self.registry.get(game_id)
                if game is None:
                    return
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
