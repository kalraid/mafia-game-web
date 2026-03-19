from __future__ import annotations

from typing import Any, Dict, TypedDict

from backend.agents.player_agent import AgentInput, AgentOutput, PlayerAgent
from backend.game.engine import GameEngine
from backend.models.game import GameState, Phase

from langgraph.graph import StateGraph, END


class AgentGraph:
    """
    LangGraph 도입 전, 단일 프로세스에서 Agent 실행 흐름을 흉내 내는 스켈레톤.
    이후 Phase에서 실제 LangGraph 노드/에지 정의로 교체 예정.
    """

    def __init__(self, engine: GameEngine, agents: Dict[str, PlayerAgent]) -> None:
        self.engine = engine
        self.agents = agents

        class _DayChatState(TypedDict):
            agent: Any
            agent_input: AgentInput
            agent_output: AgentOutput

        async def _run_agent_node(state: _DayChatState) -> Dict[str, AgentOutput]:
            output = await state["agent"].run(state["agent_input"])
            return {"agent_output": output}

        day_chat_graph = StateGraph(_DayChatState)
        day_chat_graph.add_node("run_agent", _run_agent_node)
        day_chat_graph.set_entry_point("run_agent")
        day_chat_graph.add_edge("run_agent", END)
        self._day_chat_graph = day_chat_graph.compile()

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
            graph_state = await self._day_chat_graph.ainvoke(
                {
                    "agent": agent,
                    "agent_input": agent_input,
                }
            )
            results[agent_id] = graph_state["agent_output"]

        return results
