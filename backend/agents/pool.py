from __future__ import annotations

from typing import Dict, Iterable, List

from backend.agents.persona import AgentPersona, DEFAULT_PERSONAS
from backend.agents.player_agent import PlayerAgent
from backend.models.game import Player


class AgentPool:
    def __init__(self) -> None:
        self._agents: Dict[str, PlayerAgent] = {}

    def create_agents(self, players: Iterable[Player]) -> None:
        personas_cycle: List[AgentPersona] = list(DEFAULT_PERSONAS)
        if not personas_cycle:
            return

        idx = 0
        for player in players:
            persona = personas_cycle[idx % len(personas_cycle)]
            agent_id = player.id
            self._agents[agent_id] = PlayerAgent(
                agent_id=agent_id,
                persona=persona,
                player=player,
            )
            idx += 1

    def get(self, agent_id: str) -> PlayerAgent:
        return self._agents[agent_id]

    def all_agents(self) -> Iterable[PlayerAgent]:
        return self._agents.values()
