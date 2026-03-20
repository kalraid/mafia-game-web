from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.agents.persona import AgentPersona
from backend.rag.retriever import SituationDescription, StrategyRetriever
from backend.rag.store import RAGStore
from backend.models.game import GameState, Player
from backend.models.game import Role, Phase
from backend.mcp.tools import MCPGameTools


try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    BaseModel = object  # type: ignore
    Field = None  # type: ignore


class AgentDecision(BaseModel):
    speech: Optional[str] = None
    vote_target: Optional[str] = None
    ability: Optional[str] = None
    ability_target: Optional[str] = None
    reasoning: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


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
    _rag_retriever: StrategyRetriever | None = None

    def __init__(
        self,
        agent_id: str,
        persona: AgentPersona,
        player: Player,
        mcp_tools: MCPGameTools | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.persona = persona
        self.player = player
        self.mcp_tools = mcp_tools

    def _get_rag_retriever(self) -> StrategyRetriever | None:
        """
        비용이 큰 RAG 초기화를 매 호출마다 하지 않도록 lazy singleton으로 유지.
        """
        if PlayerAgent._rag_retriever is not None:
            return PlayerAgent._rag_retriever

        try:
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./backend/rag/chroma_db")
            embedding_model = os.getenv(
                "EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            )
            store = RAGStore(persist_dir=persist_dir, embedding_model=embedding_model)
            knowledge_dir = os.getenv("RAG_KNOWLEDGE_DIR", "./docs/rag_knowledge")
            store.index_from_disk(knowledge_root=knowledge_dir)
            PlayerAgent._rag_retriever = StrategyRetriever(store=store)
            return PlayerAgent._rag_retriever
        except Exception:
            return None

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        # Phase 2 핵심: LLM 연동(키가 없으면 안전 폴백)
        decision, executed_tools = await self._decide_with_llm(agent_input)

        # Tool을 통해 GameState를 이미 갱신한 경우, 여기서는 output 필드를 비워
        # AgentGraph의 수동 MCP 호출(중복 반영)을 막는다.
        if executed_tools:
            return AgentOutput(
                speech=None,
                action=None,
                vote=None,
                internal_notes=decision.reasoning,
            )

        # Phase별로 허용된 필드만 남겨서 "엉뚱한 행동"이 섞이지 않게 가드.
        phase = agent_input.game_state.phase
        if phase == Phase.DAY_CHAT:
            speech = decision.speech
            vote_target = None
            ability = None
            ability_target = None
        elif phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
            speech = None
            vote_target = decision.vote_target
            ability = None
            ability_target = None
        elif phase == Phase.NIGHT_MAFIA:
            # 밤 마피아 협의: speech만 허용(투표/능력 금지)
            speech = decision.speech
            vote_target = None
            ability = None
            ability_target = None
        else:
            speech = decision.speech
            vote_target = decision.vote_target
            ability = decision.ability
            ability_target = decision.ability_target

        out = AgentOutput(
            speech=speech,
            action=(
                {"type": ability, "target": ability_target}
                if ability is not None and ability_target is not None
                else None
            ),
            vote=vote_target,
            internal_notes=decision.reasoning,
        )

        # C-2: AgentGraph에서 수동 MCP 호출을 제거했으므로,
        # PlayerAgent가 side-effect(채팅/투표/능력)를 직접 수행한다.
        if self.mcp_tools is not None:
            if out.speech:
                channel = "mafia_secret" if phase == Phase.NIGHT_MAFIA else "global"
                self.mcp_tools.send_chat(
                    agent_id=self.player.id,
                    content=out.speech,
                    channel=channel,
                )
            if out.vote:
                self.mcp_tools.submit_vote(
                    agent_id=self.player.id,
                    target_id=out.vote,
                )
            if out.action:
                ability_type = out.action.get("type")
                ability_target = out.action.get("target")
                if ability_type and ability_target:
                    self.mcp_tools.use_ability(
                        agent_id=self.player.id,
                        ability=ability_type,
                        target_id=ability_target,
                    )

        return out

    async def _decide_with_llm(self, agent_input: AgentInput) -> tuple[AgentDecision, bool]:
        phase = agent_input.game_state.phase
        game_state = agent_input.game_state

        # 기본 후보(스텁용)
        alive_ids = [p.id for p in game_state.players if p.is_alive]
        ai_alive_ids = [p.id for p in game_state.players if p.is_alive and not p.is_human]

        def fallback() -> AgentDecision:
            if phase == Phase.DAY_CHAT:
                return AgentDecision(
                    speech=f"{self.player.name}은(는) 현재 상황을 더 지켜보자고 말합니다.",
                    reasoning="fallback: missing LLM config or runtime error",
                    confidence=0.0,
                )
            if phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
                target = random.choice(alive_ids) if alive_ids else None
                return AgentDecision(
                    vote_target=target,
                    reasoning="fallback: random vote target",
                    confidence=0.0,
                )
            if phase == Phase.NIGHT_MAFIA:
                return AgentDecision(
                    speech=f"마피아로서의 합의를 이어가자. 다음 타겟을 정하자.",
                    reasoning="fallback: night mafia speech only",
                    confidence=0.0,
                )
            if phase == Phase.NIGHT_ABILITY:
                allowed = self._allowed_ability_for_role(self.player.role)
                if not allowed:
                    return AgentDecision(
                        ability=None,
                        ability_target=None,
                        reasoning="fallback: no ability for this role",
                        confidence=0.0,
                    )
                ability = allowed[0]
                target = random.choice(alive_ids) if alive_ids else None
                return AgentDecision(
                    ability=ability,
                    ability_target=target,
                    reasoning="fallback: random ability target",
                    confidence=0.0,
                )
            return AgentDecision(
                speech=None,
                reasoning="fallback: unsupported phase",
                confidence=0.0,
            )

        # CI/테스트에서는 LLM 호출을 강제로 끄고(폴백 사용), 실제 게임 진행에서는 켤 수 있게 제어.
        # - CI가 설정된 경우: 폴백 전용
        # - MAFIA_USE_LLM=0/false/no: 폴백 전용
        use_llm_flag = os.getenv("MAFIA_USE_LLM", "1").strip().lower()
        llm_disabled = os.getenv("CI") is not None or use_llm_flag in {"0", "false", "no"}
        if llm_disabled:
            return fallback(), False

        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return fallback(), False

        # Lazy import to avoid hard failure when env doesn't have optional deps
        try:
            from langchain_anthropic import ChatAnthropic
            from langchain_core.messages import SystemMessage, HumanMessage
            from langchain_core.tools import tool
        except Exception:
            return fallback(), False

        try:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4")
            llm = ChatAnthropic(model=model_name, temperature=0, api_key=api_key)
        except Exception:
            return fallback(), False

        # Phase별 간단한 출력 스키마 유도 (structured output 경로용)
        structured_system_prompt = (
            "너는 AI 마피아 게임 에이전트다. 아래 지시에 따라 반드시 JSON 스키마로만 답한다."
            " 말투는 persona의 speech_style을 따른다."
        )

        # Tool 호출 경로용 프롬프트
        tool_system_prompt = (
            "너는 AI 마피아 게임 에이전트다. 반드시 제공된 tool을 호출해 게임 상태를 변경하라."
            " tool 외의 일반 텍스트는 출력하지 말라."
        )

        directive_hint = agent_input.supervisor_directive or ""
        recent_chat = [
            f"{m.sender}({m.channel}): {m.content}"
            for m in game_state.chat_history[-agent_input.chat_history_limit :]
        ]

        available_players = ", ".join(alive_ids) if alive_ids else "(none)"
        my_role = self.player.role.value

        # RAG 컨텍스트 주입(문서가 없으면 빈 결과 → fallback처럼 동작)
        rag_context: list[dict] = []
        try:
            retriever = self._get_rag_retriever()
            if retriever is not None:
                alive_players = [p for p in game_state.players if p.is_alive]
                mafia_count = sum(1 for p in alive_players if p.team.value == "mafia")
                citizen_count = sum(1 for p in alive_players if p.team.value != "mafia")
                situation_text = (
                    f"game_id={game_state.game_id}, phase={phase.value}, round={game_state.round}. "
                    f"alive: mafia={mafia_count}, citizen_or_neutral={citizen_count}. "
                    f"my_role={my_role}. directive_hint={directive_hint[:200]}"
                )
                rag_context = retriever.retrieve_strategies(
                    situation=SituationDescription(text=situation_text),
                    k=3,
                )
        except Exception:
            rag_context = []

        phase_instruction = ""
        if phase == Phase.DAY_CHAT:
            phase_instruction = (
                "현재 Phase는 낮 채팅이다. speech만 작성하고 vote/ability 필드는 null로 둬라."
            )
        elif phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
            phase_instruction = "현재 Phase는 낮 투표이다. alive한 player_id 중 vote_target을 선택해라."
        elif phase == Phase.NIGHT_MAFIA:
            phase_instruction = (
                "현재 Phase는 밤 마피아 협의이다. speech만 작성해라(마피아 협의 채널). "
                "vote/ability 필드는 null로 둬라."
            )
        elif phase == Phase.NIGHT_ABILITY:
            allowed = self._allowed_ability_for_role(self.player.role)
            if not allowed:
                phase_instruction = (
                    "현재 Phase는 밤 능력 사용이다. 이 역할은 능력이 없으니 ability와 ability_target은 null로 두고, "
                    "reasoning에는 '능력 없음'이라고 적어라."
                )
            else:
                phase_instruction = (
                    f"현재 Phase는 밤 능력 사용이다. ability는 {allowed} 중 하나를 선택하고, "
                    f"ability_target은 alive한 player_id 중 하나를 선택해라."
                )
        else:
            phase_instruction = "현재 Phase에 맞는 행동을 선택해라. 해당 필드만 채우고 나머지는 null로 둬라."

        human_prompt = {
            "persona": {
                "name": self.persona.name,
                "speech_style": self.persona.speech_style,
                "aggression": self.persona.aggression,
                "trust_tendency": self.persona.trust_tendency,
                "verbosity": self.persona.verbosity,
                "logic_style": self.persona.logic_style,
            },
            "my_player": {"id": self.player.id, "name": self.player.name, "role": my_role, "team": self.player.team.value},
            "game": {
                "game_id": game_state.game_id,
                "phase": phase.value,
                "round": game_state.round,
                "timer_seconds": game_state.timer_seconds,
            },
            "supervisor_directive": directive_hint,
            "rag_context": rag_context,
            "recent_chat": recent_chat,
            "available_players": available_players,
            "task": phase_instruction,
        }

        # structured output/ tool path에서 각각 messages를 따로 구성하므로 여기서는 미사용.

        try:
            # C-2: MCP tool을 "실제로 실행"하는 경로를 우선 시도한다.
            if self.mcp_tools is not None:
                channel = "mafia_secret" if phase == Phase.NIGHT_MAFIA else "global"

                # side-effect 실제 실행용 함수(툴 래퍼는 LLM 호출용 스키마만 제공)
                def _send_chat(content: str) -> bool:
                    self.mcp_tools.send_chat(
                        agent_id=self.player.id,
                        content=content,
                        channel=channel,
                    )
                    return True

                def _submit_vote(target_id: str) -> bool:
                    self.mcp_tools.submit_vote(
                        voter_id=self.player.id,
                        target_id=target_id,
                    )
                    return True

                def _use_ability(ability: str, target_id: str) -> bool:
                    self.mcp_tools.use_ability(
                        agent_id=self.player.id,
                        ability=ability,
                        target_id=target_id,
                    )
                    return True

                @tool
                def send_chat(content: str) -> bool:
                    """발언을 전송한다."""
                    return _send_chat(content)

                @tool
                def submit_vote(target_id: str) -> bool:
                    """투표를 제출한다."""
                    return _submit_vote(target_id)

                @tool
                def use_ability(ability: str, target_id: str) -> bool:
                    """능력을 사용한다."""
                    return _use_ability(ability, target_id)

                tool_llm = llm.bind_tools([send_chat, submit_vote, use_ability])
                tool_messages = [SystemMessage(content=tool_system_prompt), HumanMessage(content=str(human_prompt))]
                tool_msg = await asyncio.to_thread(tool_llm.invoke, tool_messages)
                tool_calls = getattr(tool_msg, "tool_calls", []) or []

                # C-2 핵심: LLM이 선택한 tool_calls를 실제로 실행해 GameState를 갱신한다.
                executed_any = False
                for tc in tool_calls:
                    name = str(tc.get("name", ""))
                    args = tc.get("args", {}) or {}
                    if not isinstance(args, dict):
                        continue
                    try:
                        if name == "send_chat" and "content" in args and phase in (Phase.DAY_CHAT, Phase.NIGHT_MAFIA, Phase.NIGHT_ABILITY):
                            _send_chat(str(args["content"]).strip())
                            executed_any = True
                        elif name == "submit_vote" and "target_id" in args and phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
                            _submit_vote(str(args["target_id"]).strip())
                            executed_any = True
                        elif (
                            name == "use_ability"
                            and "ability" in args
                            and "target_id" in args
                            and phase == Phase.NIGHT_ABILITY
                        ):
                            _use_ability(str(args["ability"]).strip(), str(args["target_id"]).strip())
                            executed_any = True
                    except Exception:
                        # 도구 실행 실패는 폴백으로 처리한다.
                        executed_any = False
                        break

                decision = self._decision_from_tool_calls(tool_calls=tool_calls, phase=phase)
                if decision is not None and executed_any:
                    return decision, True

            structured_llm = llm.with_structured_output(AgentDecision)
            messages = [SystemMessage(content=structured_system_prompt), HumanMessage(content=str(human_prompt))]
            decision: AgentDecision = await asyncio.to_thread(structured_llm.invoke, messages)
            return decision, False
        except Exception:
            return fallback(), False

    def _decision_from_tool_calls(self, tool_calls: list[dict], phase: Phase) -> AgentDecision | None:
        if not tool_calls:
            return None

        speech: str | None = None
        vote_target: str | None = None
        ability: str | None = None
        ability_target: str | None = None

        tool_names: list[str] = []
        for tc in tool_calls:
            name = str(tc.get("name", ""))
            tool_names.append(name)
            args = tc.get("args", {}) or {}
            if not isinstance(args, dict):
                continue

            if name == "send_chat" and phase in (Phase.DAY_CHAT, Phase.NIGHT_MAFIA):
                content = str(args.get("content", "")).strip()
                if content:
                    speech = content
            elif name == "submit_vote" and phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
                target_id = str(args.get("target_id", "")).strip()
                if target_id:
                    vote_target = target_id
            elif name == "use_ability" and phase == Phase.NIGHT_ABILITY:
                ability = str(args.get("ability", "")).strip() or ability
                ability_target = str(args.get("target_id", "")).strip() or ability_target

        return AgentDecision(
            speech=speech,
            vote_target=vote_target,
            ability=ability,
            ability_target=ability_target,
            reasoning=f"tool_call: {', '.join(tool_names)}",
            confidence=0.7,
        )

    def _allowed_ability_for_role(self, role: Role) -> list[str]:
        # GAME_RULES 기준 최소 매핑 (추후 더 정교화)
        if role == Role.DETECTIVE:
            return ["investigate"]
        if role == Role.DOCTOR:
            return ["heal"]
        if role == Role.MAFIA:
            return ["attack"]
        if role == Role.KILLER:
            return ["attack"]
        if role == Role.FORTUNE_TELLER:
            return ["investigate"]
        if role == Role.SPY:
            return ["spy_listen"]
        if role in (Role.JESTER, Role.CITIZEN):
            return []
        return ["investigate"]
