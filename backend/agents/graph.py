from __future__ import annotations

from typing import Any, Dict, TypedDict

from backend.agents.player_agent import AgentInput, AgentOutput, PlayerAgent
from backend.game.engine import GameEngine
from backend.mcp.tools import MCPGameTools
from backend.supervisors.citizen import CitizenSupervisor
from backend.supervisors.mafia import MafiaSupervisor
from backend.supervisors.neutral import NeutralSupervisor
from backend.models.game import GameState, Phase

from langgraph.graph import StateGraph, END


class AgentGraph:
    """
    LangGraph 도입 전, 단일 프로세스에서 Agent 실행 흐름을 흉내 내는 스켈레톤.
    이후 Phase에서 실제 LangGraph 노드/에지 정의로 교체 예정.
    """

    def __init__(
        self,
        engine: GameEngine,
        agents: Dict[str, PlayerAgent],
        citizen_supervisor: CitizenSupervisor | None = None,
        mafia_supervisor: MafiaSupervisor | None = None,
        neutral_supervisor: NeutralSupervisor | None = None,
    ) -> None:
        self.engine = engine
        self.agents = agents
        self.mcp_tools = MCPGameTools(engine=self.engine)
        self.citizen_supervisor = citizen_supervisor or CitizenSupervisor()
        self.mafia_supervisor = mafia_supervisor or MafiaSupervisor()
        self.neutral_supervisor = neutral_supervisor or NeutralSupervisor()

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
        self._agent_call_graph = day_chat_graph.compile()

    def _issue_directives_for_phase(self, state: GameState) -> None:
        """
        Phase 진입 시 슈퍼바이저가 state.directives를 채운다.
        (현재는 L2 Redis/A2A 루프까지는 아니고, Agent 입력 주입만 MVP로 연결)
        """
        state.directives = []

        # Day 계열: speech/vote 모두 동일하게 시민/마피아/중립 지시를 먼저 주입
        if state.phase in (
            Phase.DAY_CHAT,
            Phase.DAY_VOTE,
            Phase.FINAL_SPEECH,
            Phase.FINAL_VOTE,
        ):
            state.directives.extend(self.citizen_supervisor.issue_directives(state, reports=[]))
            state.directives.extend(self.mafia_supervisor.issue_concealment_directives(state))
            state.directives.extend(self.neutral_supervisor.issue_directives(state, reports=[]))
            return

        # Night 계열: 능력 사용 지시 (Phase.NIGHT_ABILITY에서만 의미 있게 적용)
        if state.phase == Phase.NIGHT_ABILITY:
            # citizen/mafia/neutral이 ability_strategy directive를 생성하도록 확장 예정
            if hasattr(self.citizen_supervisor, "issue_night_ability_directives"):
                state.directives.extend(self.citizen_supervisor.issue_night_ability_directives(state, reports=[]))  # type: ignore[attr-defined]
            if hasattr(self.mafia_supervisor, "issue_night_ability_directives"):
                state.directives.extend(self.mafia_supervisor.issue_night_ability_directives(state))  # type: ignore[attr-defined]
            if hasattr(self.neutral_supervisor, "issue_night_ability_directives"):
                state.directives.extend(self.neutral_supervisor.issue_night_ability_directives(state, reports=[]))  # type: ignore[attr-defined]
            return

        # 그 외 phase는 directive 없음
        return

    def _directive_hint_for_agent(self, state: GameState, agent_id: str) -> str | None:
        directives = [d for d in state.directives if d.target_agent == agent_id]
        if not directives:
            return None
        # priority 기준으로 먼저 정렬
        priority_order = {"high": 0, "medium": 1, "low": 2}
        directives.sort(key=lambda d: priority_order.get(getattr(d, "priority", "medium"), 1))
        return "\n".join(d.content for d in directives)

    async def run_day_chat_round(self, state: GameState) -> Dict[str, AgentOutput]:
        if state.phase != Phase.DAY_CHAT:
            return {}

        self._issue_directives_for_phase(state)

        results: Dict[str, AgentOutput] = {}
        for agent_id, agent in self.agents.items():
            player = agent.player
            if not player.is_alive:
                continue

            agent_input = AgentInput(
                game_state=state,
                my_state=player,
                supervisor_directive=self._directive_hint_for_agent(state, agent_id),
            )
            graph_state = await self._agent_call_graph.ainvoke(
                {
                    "agent": agent,
                    "agent_input": agent_input,
                }
            )
            output: AgentOutput = graph_state["agent_output"]

            # Agent output → MCP tool calls (GameState 업데이트)
            if output.speech:
                self.mcp_tools.send_chat(agent_id=agent_id, content=output.speech, channel="global")
            if output.vote:
                self.mcp_tools.submit_vote(agent_id=agent_id, target_id=output.vote)
            if output.action:
                ability_type = output.action.get("type")
                ability_target = output.action.get("target")
                if ability_type and ability_target:
                    self.mcp_tools.use_ability(
                        agent_id=agent_id,
                        ability=ability_type,
                        target_id=ability_target,
                    )

            results[agent_id] = output

        return results

    async def run_vote_round(self, state: GameState) -> Dict[str, AgentOutput]:
        if state.phase not in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
            return {}

        self._issue_directives_for_phase(state)
        results: Dict[str, AgentOutput] = {}
        for agent_id, agent in self.agents.items():
            player = agent.player
            if not player.is_alive:
                continue
            agent_input = AgentInput(
                game_state=state,
                my_state=player,
                supervisor_directive=self._directive_hint_for_agent(state, agent_id),
            )
            graph_state = await self._agent_call_graph.ainvoke(
                {"agent": agent, "agent_input": agent_input}
            )
            output: AgentOutput = graph_state["agent_output"]

            if output.vote:
                self.mcp_tools.submit_vote(agent_id=agent_id, target_id=output.vote)
            if output.speech:
                self.mcp_tools.send_chat(agent_id=agent_id, content=output.speech, channel="global")

            if output.action:
                ability_type = output.action.get("type")
                ability_target = output.action.get("target")
                if ability_type and ability_target:
                    self.mcp_tools.use_ability(
                        agent_id=agent_id,
                        ability=ability_type,
                        target_id=ability_target,
                    )

            results[agent_id] = output
        return results

    async def run_night_ability_round(self, state: GameState) -> Dict[str, AgentOutput]:
        if state.phase != Phase.NIGHT_ABILITY:
            return {}

        self._issue_directives_for_phase(state)
        results: Dict[str, AgentOutput] = {}
        for agent_id, agent in self.agents.items():
            player = agent.player
            if not player.is_alive:
                continue
            agent_input = AgentInput(
                game_state=state,
                my_state=player,
                supervisor_directive=self._directive_hint_for_agent(state, agent_id),
            )
            graph_state = await self._agent_call_graph.ainvoke(
                {"agent": agent, "agent_input": agent_input}
            )
            output: AgentOutput = graph_state["agent_output"]

            if output.action:
                ability_type = output.action.get("type")
                ability_target = output.action.get("target")
                if ability_type and ability_target:
                    self.mcp_tools.use_ability(
                        agent_id=agent_id,
                        ability=ability_type,
                        target_id=ability_target,
                    )
            if output.speech:
                # 밤에도 발언을 허용할지 여부는 이후 WebSocket 채널 규칙으로 분리
                self.mcp_tools.send_chat(agent_id=agent_id, content=output.speech, channel="global")

            results[agent_id] = output
        return results
