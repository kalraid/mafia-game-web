from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import Dict, Optional, TypedDict

logger = logging.getLogger("mafia.backend.agents.graph")

from backend.agents.player_agent import AgentInput, AgentOutput, PlayerAgent
from backend.game.engine import GameEngine
from backend.pod import POD_ID
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
        self.citizen_supervisor = citizen_supervisor or CitizenSupervisor()
        self.mafia_supervisor = mafia_supervisor or MafiaSupervisor()
        self.neutral_supervisor = neutral_supervisor or NeutralSupervisor()

        logger.info(
            "[POD=%s] AgentGraph 초기화 — game_id=%s"
            " supervisors=[CitizenSupervisor, MafiaSupervisor, NeutralSupervisor]"
            " agents=%s  ← 이 POD가 전담 실행",
            POD_ID,
            engine.state.game_id,
            list(agents.keys()),
        )

        class _AgentCallState(TypedDict):
            agent_id: str
            supervisor_directive: Optional[str]
            agent_output: Dict[str, object]

        async def _run_agent_node(state: _AgentCallState) -> Dict[str, Dict[str, object]]:
            agent_id = state.get("agent_id", "")
            if not agent_id:
                raise ValueError("_run_agent_node: agent_id가 비어 있습니다.")
            agent = self.agents.get(agent_id)
            if agent is None:
                raise ValueError(f"_run_agent_node: 알 수 없는 agent_id={agent_id!r}")
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
                    "rag_context": output.rag_context,
                }
            }

        day_chat_graph = StateGraph(_AgentCallState)
        day_chat_graph.add_node("run_agent", _run_agent_node)
        day_chat_graph.set_entry_point("run_agent")
        day_chat_graph.add_edge("run_agent", END)
        # C-5: MAFIA_USE_REDIS_CHECKPOINTER=1 이면 RedisSaver 사용, 실패 시 로그 후 raise.
        # 비활성화 시 compile()만 사용. thread_id는 _invoke_agent의 ainvoke(config)에서 전달.
        self._agent_call_graph = self._compile_agent_graph(day_chat_graph)

    def _compile_agent_graph(self, graph: StateGraph) -> object:
        use_redis = os.getenv("MAFIA_USE_REDIS_CHECKPOINTER", "0").strip().lower()
        if use_redis not in {"1", "true", "yes"}:
            return graph.compile()

        # C-5: 폴백 제거. Redis 체크포인트 활성화 시 실패는 로깅 후 에러 전파.
        import logging

        logger = logging.getLogger("mafia.backend")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        import redis
        from langgraph.checkpoint.redis import RedisSaver

        try:
            redis_client = redis.from_url(
                redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=False,
            )
            checkpointer = RedisSaver(redis_client)
            setup_fn = getattr(checkpointer, "setup", None)
            if callable(setup_fn):
                setup_fn()
            return graph.compile(checkpointer=checkpointer)
        except Exception as e:
            logger.exception("Redis Checkpointer compile/setup 실패: %s", e)
            raise

    def _issue_directives_for_phase(self, state: GameState) -> None:
        """
        Phase 진입 시 슈퍼바이저가 state.directives를 채운다.
        (현재는 L2 Redis/A2A 루프까지는 아니고, Agent 입력 주입만 MVP로 연결)
        """
        state.directives = []
        reports_snapshot = list(state.reports)

        logger.info(
            "[POD=%s] Supervisor 지시문 발행 — game_id=%s phase=%s round=%d"
            " citizen_supervisor=active mafia_supervisor=active neutral_supervisor=active",
            POD_ID,
            state.game_id,
            state.phase.value,
            state.round,
        )

        # Day 계열: speech/vote 모두 동일하게 시민/마피아/중립 지시를 먼저 주입
        if state.phase in (
            Phase.DAY_CHAT,
            Phase.DAY_VOTE,
            Phase.FINAL_SPEECH,
            Phase.FINAL_VOTE,
        ):
            directives = self.citizen_supervisor.issue_directives(state, reports=reports_snapshot)
            logger.debug(
                "[POD=%s] CitizenSupervisor → directives=%d targets=%s",
                POD_ID,
                len(directives),
                [d.target_agent for d in directives],
            )
            state.directives.extend(directives)

            directives = self.mafia_supervisor.issue_concealment_directives(state, reports=reports_snapshot)
            logger.debug(
                "[POD=%s] MafiaSupervisor → directives=%d targets=%s",
                POD_ID,
                len(directives),
                [d.target_agent for d in directives],
            )
            state.directives.extend(directives)

            directives = self.neutral_supervisor.issue_directives(state, reports=reports_snapshot)
            logger.debug(
                "[POD=%s] NeutralSupervisor → directives=%d targets=%s",
                POD_ID,
                len(directives),
                [d.target_agent for d in directives],
            )
            state.directives.extend(directives)
            return

        # Night 계열: 마피아 협의 (NIGHT_MAFIA) / 능력 사용 (NIGHT_ABILITY)
        if state.phase == Phase.NIGHT_MAFIA:
            # 마피아 쪽만 실제로 발언하도록 GameRunner/실행 로직에서 필터링한다.
            # 여기서는 마피아가 참고할 전략/은폐 지시를 우선 주입한다.
            directives = self.mafia_supervisor.issue_concealment_directives(state, reports=reports_snapshot)
            logger.debug(
                "[POD=%s] MafiaSupervisor → directives=%d targets=%s",
                POD_ID,
                len(directives),
                [d.target_agent for d in directives],
            )
            state.directives.extend(directives)
            return

        if state.phase == Phase.NIGHT_ABILITY:
            # citizen/mafia/neutral이 ability_strategy directive를 생성하도록 확장 예정
            if hasattr(self.citizen_supervisor, "issue_night_ability_directives"):
                directives = self.citizen_supervisor.issue_night_ability_directives(  # type: ignore[attr-defined]
                    state, reports=reports_snapshot
                )
                logger.debug(
                    "[POD=%s] CitizenSupervisor(night_ability) → directives=%d targets=%s",
                    POD_ID,
                    len(directives),
                    [d.target_agent for d in directives],
                )
                state.directives.extend(directives)
            if hasattr(self.mafia_supervisor, "issue_night_ability_directives"):
                directives = self.mafia_supervisor.issue_night_ability_directives(  # type: ignore[attr-defined]
                    state, reports=reports_snapshot
                )
                logger.debug(
                    "[POD=%s] MafiaSupervisor(night_ability) → directives=%d targets=%s",
                    POD_ID,
                    len(directives),
                    [d.target_agent for d in directives],
                )
                state.directives.extend(directives)
            if hasattr(self.neutral_supervisor, "issue_night_ability_directives"):
                directives = self.neutral_supervisor.issue_night_ability_directives(  # type: ignore[attr-defined]
                    state, reports=reports_snapshot
                )
                logger.debug(
                    "[POD=%s] NeutralSupervisor(night_ability) → directives=%d targets=%s",
                    POD_ID,
                    len(directives),
                    [d.target_agent for d in directives],
                )
                state.directives.extend(directives)
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

    def supervisor_replan(self, state: GameState) -> None:
        """
        C-8: Phase 종료 후 슈퍼바이저가 상태를 재진단.
        MVP로는 `state.reports` 텍스트에 포함된 키워드를 바탕으로
        대상 플레이어의 trust_score를 보정한다.

        - '마피아/mafia' 언급: trust_score 낮춤
        - '시민/citizen' 언급: trust_score 올림
        """
        logger.info("supervisor_replan round=%s", state.round)
        if not state.reports:
            return

        # 간단한 키워드 기반 보정 (구체화는 이후 단계에서)
        for r in list(state.reports):
            content = (r.content or "").lower()
            if not content.strip():
                continue

            is_mafia = "mafia" in content or "마피아" in content
            is_citizen = "citizen" in content or "시민" in content
            if not (is_mafia or is_citizen):
                continue

            for p in state.players:
                # Report content에 id/name이 포함되었다고 가정
                token_hits = (p.id.lower() in content) or (p.name.lower() in content)
                if not token_hits:
                    continue

                if is_mafia:
                    p.trust_score = max(0.0, min(p.trust_score, 0.2))
                elif is_citizen:
                    p.trust_score = max(0.0, min(1.0, max(p.trust_score, 0.8)))

        # 동일 라운드 재적용 방지
        state.reports = []

    async def _invoke_agent(self, state: GameState, agent_id: str) -> AgentOutput:
        logger.info(
            "invoke agent=%s phase=%s",
            agent_id,
            getattr(state.phase, "value", state.phase),
        )
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
        rc = out.get("rag_context")
        rag_list: list[dict] = []
        if isinstance(rc, list):
            rag_list = [x for x in rc if isinstance(x, dict)]

        return AgentOutput(
            speech=out.get("speech") if isinstance(out.get("speech"), str) else None,
            action=out.get("action") if isinstance(out.get("action"), dict) else None,
            vote=out.get("vote") if isinstance(out.get("vote"), str) else None,
            internal_notes=out.get("internal_notes") if isinstance(out.get("internal_notes"), str) else None,
            rag_context=rag_list,
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

            results[agent_id] = output

        return results
