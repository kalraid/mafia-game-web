from __future__ import annotations

from typing import Dict

from backend.agents.player_agent import AgentInput, AgentOutput, PlayerAgent
from backend.game.engine import GameEngine
from backend.models.game import GameState, Phase


class AgentGraph:
    """
    LangGraph 도입 전, 단일 프로세스에서 Agent 실행 흐름을 흉내 내는 스켈레톤.
    이후 Phase에서 실제 LangGraph 노드/에지 정의로 교체 예정.
    """

    def __init__(self, engine: GameEngine, agents: Dict[str, PlayerAgent]) -> None:
        self.engine = engine
        self.agents = agents

    async def run_day_chat_round(self, state: GameState) -> Dict[str, AgentOutput]:
        if state.phase != Phase.DAY_CHAT:
            return {}

        results: Dict[str, AgentOutput] = {}
        for agent_id, agent in self.agents.items():
            player = agent.player
            if not player.is_alive:
                continue

            agent_input = AgentInput(
                game_state=state,
                my_state=player,
                supervisor_directive=None,
            )
            results[agent_id] = await agent.run(agent_input)

        return results
