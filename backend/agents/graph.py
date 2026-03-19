from __future__ import annotations

import asyncio
import os
import random
from typing import Dict, Optional, TypedDict

from backend.agents.player_agent import AgentInput, AgentOutput, PlayerAgent
from backend.game.engine import GameEngine
from backend.mcp.tools import MCPGameTools
from backend.supervisors.citizen import CitizenSupervisor
from backend.supervisors.mafia import MafiaSupervisor
from backend.supervisors.neutral import NeutralSupervisor
from backend.models.game import GameState, Phase, Team

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

        class _AgentCallState(TypedDict):
            agent_id: str
            supervisor_directive: Optional[str]
            agent_output: Dict[str, object]

        async def _run_agent_node(state: _AgentCallState) -> Dict[str, Dict[str, object]]:
            agent_id = state["agent_id"]
            agent = self.agents[agent_id]
            agent_input = AgentInput(
                game_state=self.engine.state,
                my_state=agent.player,
                supervisor_directive=state.get("supervisor_directive"),
            )
            output = await agent.run(agent_input)
            return {
                "agent_output": {
                    "speech": output.speech,
                    "action": output.action,
                    "vote": output.vote,
                    "internal_notes": output.internal_notes,
                }
            }

        day_chat_graph = StateGraph(_AgentCallState)
        day_chat_graph.add_node("run_agent", _run_agent_node)
        day_chat_graph.set_entry_point("run_agent")
        day_chat_graph.add_edge("run_agent", END)
        # C-5: Redis checkpointer를 우선 시도하고, 실패 시 일반 compile로 폴백.
        # thread_id는 ainvoke(config)에서 game_id+agent_id 조합으로 전달.
        self._agent_call_graph = self._compile_agent_graph(day_chat_graph)

    def _compile_agent_graph(self, graph: StateGraph) -> object:
        if os.getenv("MAFIA_USE_REDIS_CHECKPOINTER", "0").strip().lower() not in {"1", "true", "yes"}:
            return graph.compile()

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            import redis
            from langgraph.checkpoint.redis import RedisSaver

            redis_client = redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
            checkpointer = RedisSaver(redis_client)
            setup_fn = getattr(checkpointer, "setup", None)
            if callable(setup_fn):
                setup_fn()
            return graph.compile(checkpointer=checkpointer)
        except Exception:
            return graph.compile()

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

        # Night 계열: 마피아 협의 (NIGHT_MAFIA) / 능력 사용 (NIGHT_ABILITY)
        if state.phase == Phase.NIGHT_MAFIA:
            # 마피아 쪽만 실제로 발언하도록 GameRunner/실행 로직에서 필터링한다.
            # 여기서는 마피아가 참고할 전략/은폐 지시를 우선 주입한다.
            state.directives.extend(self.mafia_supervisor.issue_concealment_directives(state))
            return

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

    async def _speech_delay(self, agent: PlayerAgent) -> None:
        """persona.verbosity 기반 발언 전 딜레이. CI/테스트는 최소화."""
        if os.getenv("CI") or os.getenv("MAFIA_USE_LLM", "1").strip().lower() in ("0", "false", "no"):
            await asyncio.sleep(0.05)
            return
        verbosity = getattr(agent.persona, "verbosity", 0.5)
        base = 15 * (1.0 - verbosity)
        jitter = random.uniform(0, 3)
        await asyncio.sleep(max(0.05, base + jitter))

    def _directive_hint_for_agent(self, state: GameState, agent_id: str) -> str | None:
        directives = [d for d in state.directives if d.target_agent == agent_id]
        if not directives:
            return None
        # priority 기준으로 먼저 정렬
        priority_order = {"high": 0, "medium": 1, "low": 2}
        directives.sort(key=lambda d: priority_order.get(getattr(d, "priority", "medium"), 1))
        return "\n".join(d.content for d in directives)

    async def _invoke_agent(self, state: GameState, agent_id: str) -> AgentOutput:
        config = {"configurable": {"thread_id": f"{state.game_id}_{agent_id}"}}
        graph_state = await self._agent_call_graph.ainvoke(
            {
                "agent_id": agent_id,
                "supervisor_directive": self._directive_hint_for_agent(state, agent_id),
            },
            config=config,
        )
        out = graph_state.get("agent_output", {})
        if not isinstance(out, dict):
            out = {}
        return AgentOutput(
            speech=out.get("speech") if isinstance(out.get("speech"), str) else None,
            action=out.get("action") if isinstance(out.get("action"), dict) else None,
            vote=out.get("vote") if isinstance(out.get("vote"), str) else None,
            internal_notes=out.get("internal_notes") if isinstance(out.get("internal_notes"), str) else None,
        )

    async def run_day_chat_round(self, state: GameState) -> Dict[str, AgentOutput]:
        if state.phase != Phase.DAY_CHAT:
            return {}

        self._issue_directives_for_phase(state)

        results: Dict[str, AgentOutput] = {}
        for agent_id, agent in self.agents.items():
            player = agent.player
            if not player.is_alive:
                continue

            # 발언 타이밍: verbosity 낮을수록 늦게 (과묵할수록 늦게), CI/테스트는 최소 딜레이
            await self._speech_delay(agent)
            output = await self._invoke_agent(state, agent_id)

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
            output = await self._invoke_agent(state, agent_id)

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
            output = await self._invoke_agent(state, agent_id)

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

    async def run_night_mafia_round(self, state: GameState) -> Dict[str, AgentOutput]:
        if state.phase != Phase.NIGHT_MAFIA:
            return {}

        self._issue_directives_for_phase(state)

        results: Dict[str, AgentOutput] = {}
        for agent_id, agent in self.agents.items():
            player = agent.player
            if not player.is_alive:
                continue
            if player.team != Team.MAFIA:
                continue

            await self._speech_delay(agent)
            output = await self._invoke_agent(state, agent_id)

            if output.speech:
                # 밤 마피아 협의는 전용 채널로 브로드캐스트(프론트 스타일링용).
                self.mcp_tools.send_chat(agent_id=agent_id, content=output.speech, channel="mafia_secret")

            results[agent_id] = output

        return results
