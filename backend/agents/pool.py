from __future__ import annotations

from typing import Dict, Iterable, List

from backend.game.engine import GameEngine
from backend.mcp.tools import MCPGameTools

from backend.agents.persona import AgentPersona, DEFAULT_PERSONAS
from backend.agents.player_agent import PlayerAgent
from backend.models.game import Player


class AgentPool:
    def __init__(self) -> None:
        self._agents: Dict[str, PlayerAgent] = {}

    def create_agents(self, players: Iterable[Player], engine: GameEngine | None = None) -> None:
        personas_cycle: List[AgentPersona] = list(DEFAULT_PERSONAS)
        if not personas_cycle:
            return

        mcp_tools = MCPGameTools(engine=engine) if engine is not None else None

        idx = 0
        for player in players:
            persona = personas_cycle[idx % len(personas_cycle)]
            agent_id = player.id
            self._agents[agent_id] = PlayerAgent(
                agent_id=agent_id,
                persona=persona,
                player=player,
                mcp_tools=mcp_tools,
            )
            idx += 1

    def get(self, agent_id: str) -> PlayerAgent:
        return self._agents[agent_id]

    def all_agents(self) -> Iterable[PlayerAgent]:
        return self._agents.values()
