from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.agents.persona import AgentPersona
from backend.models.game import GameState, Player


@dataclass
class AgentInput:
    game_state: GameState
    my_state: Player
    supervisor_directive: Optional[str]
    chat_history_limit: int = 20


@dataclass
class AgentOutput:
    speech: Optional[str]
    action: Optional[dict]
    vote: Optional[str]
    internal_notes: Optional[str]


class PlayerAgent:
    def __init__(self, agent_id: str, persona: AgentPersona, player: Player) -> None:
        self.agent_id = agent_id
        self.persona = persona
        self.player = player

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        # Phase 2에서는 구조만 정의하고, 실제 LLM 연동과 전략 로직은 후속 Phase에서 구현
        return AgentOutput(
            speech=None,
            action=None,
            vote=None,
            internal_notes=None,
        )
