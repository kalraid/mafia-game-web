from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from backend.agents.graph import AgentGraph
from backend.agents.pool import AgentPool
from backend.game.engine import GameEngine
from backend.game.snapshot import build_game_state_payload, role_to_korean
from backend.models.chat import ChatMessage
from backend.models.game import Phase
from backend.websocket.events import ServerToClientEvent

from backend.models.game import Role, GameEvent


class GameRunner:
    def __init__(self, game_id: str, engine: GameEngine, ws_manager: Any) -> None:
        self.game_id = game_id
        self.engine = engine
        self.ws_manager = ws_manager

        # AgentGraph/AgentPool은 AI 플레이어가 있는 경우에만 구성
        self.agent_graph: Optional[AgentGraph] = None
        self._agent_call_ready = False

        self._last_chat_index = 0
        self._last_event_index = 0

        # 프론트 result 페이지용 사망 정보
        self._death_info: Dict[str, Dict[str, Any]] = {}

        self._task: asyncio.Task | None = None

    def ensure_agent_graph(self) -> None:
        if self._agent_call_ready:
            return

        players = [p for p in self.engine.state.players if p.is_alive]
        ai_players = [p for p in players if not p.is_human]
        if not ai_players:
            self._agent_call_ready = True
            return

        pool = AgentPool()
        pool.create_agents(players=ai_players)
        agents = {a.agent_id: a for a in pool.all_agents()}
        self.agent_graph = AgentGraph(engine=self.engine, agents=agents)
        self._agent_call_ready = True

    async def run(self) -> None:
        # 이미 winner면 시작하지 않음
        while self.engine.state.winner is None:
            # phase 입장 브로드캐스트
            self.ensure_agent_graph()
            await self._broadcast_phase_state()

            # AI 행동 실행
            await self._run_agents_for_current_phase()

            # agent 실행 후 채팅/투표 반영 브로드캐스트
            await self._broadcast_new_chats()
            await self._broadcast_phase_state()

            # 타이머 대기 후 phase 전환
            await asyncio.sleep(max(0, self.engine.state.timer_seconds))
            self.engine.advance_phase()

            # player_death 이벤트 브로드캐스트
            await self._broadcast_new_deaths()

            if self.engine.state.winner is not None:
                await self._broadcast_game_over()
                return

    async def _run_agents_for_current_phase(self) -> None:
        if self.agent_graph is None:
            return

        phase = self.engine.state.phase
        if phase == Phase.DAY_CHAT:
            await self.agent_graph.run_day_chat_round(self.engine.state)
        elif phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
            await self.agent_graph.run_vote_round(self.engine.state)
        elif phase == Phase.NIGHT_MAFIA:
            await self.agent_graph.run_night_mafia_round(self.engine.state)
        elif phase == Phase.NIGHT_ABILITY:
            await self.agent_graph.run_night_ability_round(self.engine.state)

    async def _broadcast_phase_state(self) -> None:
        payload = build_game_state_payload(self.engine, death_info=self._death_info)

        # phase_change
        await self.ws_manager.broadcast(
            self.game_id,
            ServerToClientEvent(
                event="phase_change",
                payload={"phase": payload["phase"], "round": payload["round"]},
            ),
        )
        # game_state_update
        await self.ws_manager.broadcast(
            self.game_id,
            ServerToClientEvent(
                event="game_state_update",
                payload={
                    "players": payload["players"],
                    "phase": payload["phase"],
                    "round": payload["round"],
                    "timer_seconds": payload["timer_seconds"],
                },
            ),
        )

    async def _broadcast_new_chats(self) -> None:
        # engine.state.chat_history의 신규 메시지들을 chat_broadcast로 전달
        new_msgs: list[ChatMessage] = self.engine.state.chat_history[self._last_chat_index :]
        self._last_chat_index = len(self.engine.state.chat_history)

        for msg in new_msgs:
            await self.ws_manager.broadcast(
                self.game_id,
                ServerToClientEvent(
                    event="chat_broadcast",
                    payload={
                        "sender": msg.sender if msg.sender != "system" else "System",
                        "content": msg.content,
                        "channel": msg.channel,
                        "timestamp": msg.timestamp.isoformat(),
                        "is_ai": msg.is_ai,
                    },
                ),
            )

    async def _broadcast_new_deaths(self) -> None:
        new_events: list[GameEvent] = self.engine.state.events[self._last_event_index :]
        self._last_event_index = len(self.engine.state.events)

        for e in new_events:
            if e.type != "player_death":
                continue

            player_name = e.payload.get("player")
            role_value = e.payload.get("role")
            cause_value = e.payload.get("cause")
            death_round = e.payload.get("round", "")

            # 프론트 result 페이지용 확장 필드 기록
            self._death_info[str(player_name)] = {
                "death_round": death_round,
                "death_cause": cause_value,
            }

            # WebSocket player_death
            # 프론트는 role 문자열을 바로 표시하므로 한글 매핑해서 넣는다.
            try:
                role_kor = role_to_korean(Role(str(role_value)))
            except Exception:
                role_kor = str(role_value)

            await self.ws_manager.broadcast(
                self.game_id,
                ServerToClientEvent(
                    event="player_death",
                    payload={"player": player_name, "role": role_kor, "cause": cause_value},
                ),
            )

    async def _broadcast_game_over(self) -> None:
        winner = self.engine.state.winner or "unknown"
        reason_map = {
            "citizen": "마피아가 모두 제거되었습니다.",
            "mafia": "마피아 수가 시민(중립 포함) 이상입니다.",
            "jester": "광대가 투표로 처형되었습니다.",
        }
        reason = reason_map.get(winner, "게임이 종료되었습니다.")

        payload = build_game_state_payload(self.engine, death_info=self._death_info)

        await self.ws_manager.broadcast(
            self.game_id,
            ServerToClientEvent(
                event="game_over",
                payload={
                    "winner": winner,
                    "reason": reason,
                    "players": payload["players"],
                },
            ),
        )

