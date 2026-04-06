from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.agents.persona import AgentPersona
from backend.rag.retriever import SituationDescription, StrategyRetriever
from backend.rag.store import RAGStore
from backend.models.game import GameState, Player
from backend.models.game import Role, Phase
from backend.config import get_chat_llm
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


def _rag_hits_for_client(raw: List[dict]) -> List[dict]:
    """WebSocket/JSON용으로 RAG hit를 직렬화 가능한 dict로 정규화한다."""
    out: List[dict] = []
    for item in raw:
        meta = item.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}
        out.append(
            {
                "text": str(item.get("text", "")),
                "score": float(item.get("score", 0.0)),
                "metadata": {str(k): str(v) for k, v in meta.items()},
            }
        )
    return out


@dataclass
class AgentOutput:
    speech: Optional[str]
    action: Optional[dict]
    vote: Optional[str]
    internal_notes: Optional[str]
    rag_context: List[dict] = field(default_factory=list)


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

    def _fetch_rag_context_raw(self, agent_input: AgentInput) -> list[dict]:
        """LLM 가용 여부와 무관하게 RAG 히트를 가져온다(디버그 패널·프롬프트 공용)."""
        game_state = agent_input.game_state
        phase = game_state.phase
        directive_hint = agent_input.supervisor_directive or ""
        my_role = self.player.role.value
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
        return rag_context

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        # Phase 2 핵심: LLM 연동(키가 없으면 안전 폴백)
        decision, executed_tools, rag_context = await self._decide_with_llm(agent_input)
        rag_safe = _rag_hits_for_client(rag_context)

        # Tool을 통해 GameState를 이미 갱신한 경우, 여기서는 output 필드를 비워
        # AgentGraph의 수동 MCP 호출(중복 반영)을 막는다.
        if executed_tools:
            return AgentOutput(
                speech=None,
                action=None,
                vote=None,
                internal_notes=decision.reasoning,
                rag_context=rag_safe,
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
            rag_context=rag_safe,
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

    async def _decide_with_llm(self, agent_input: AgentInput) -> tuple[AgentDecision, bool, list[dict]]:
        phase = agent_input.game_state.phase
        game_state = agent_input.game_state

        # 기본 후보(스텁용)
        alive_ids = [p.id for p in game_state.players if p.is_alive]

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
        rag_context = self._fetch_rag_context_raw(agent_input)

        use_llm_flag = os.getenv("MAFIA_USE_LLM", "1").strip().lower()
        llm_disabled = os.getenv("CI") is not None or use_llm_flag in {"0", "false", "no"}
        if llm_disabled:
            return fallback(), False, rag_context

        llm = get_chat_llm(temperature=0)
        if llm is None:
            return fallback(), False, rag_context

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            from langchain_core.tools import tool
        except Exception:
            return fallback(), False, rag_context

        # Phase별 간단한 출력 스키마 유도 (structured output 경로용)
        structured_system_prompt = (
            "너는 AI 마피아 게임 에이전트다. 아래 지시에 따라 반드시 JSON 스키마로만 답한다."
            " 말투는 persona의 speech_style을 따른다."
        )

        # Tool 호출 경로용 프롬프트
        tool_system_prompt = (
            "너는 AI 마피아 게임 에이전트다. 반드시 제공된 tool을 호출해 게임 상태를 변경하라."
            " tool 외의 일반 텍스트는 출력하지 말라."
            " report_to_supervisor(report)는 슈퍼바이저 전략 반영용 선택 도구이며, 남용하지 말라."
        )

        directive_hint = agent_input.supervisor_directive or ""
        recent_chat = [
            f"{m.sender}({m.channel}): {m.content}"
            for m in game_state.chat_history[-agent_input.chat_history_limit :]
        ]

        available_players = ", ".join(alive_ids) if alive_ids else "(none)"
        my_role = self.player.role.value

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

        if phase in {
            Phase.DAY_CHAT,
            Phase.DAY_VOTE,
            Phase.FINAL_VOTE,
            Phase.NIGHT_MAFIA,
            Phase.NIGHT_ABILITY,
        }:
            phase_instruction += (
                " 필요 시 report_to_supervisor(report=...) 도구로 슈퍼바이저에 짧은 관찰·의심을 보고할 수 있다."
                " 턴당 최대 1회 권장이며, 빈 보고·무의미한 반복 호출은 하지 말라."
            )

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
                        agent_id=self.player.id,
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

                def _report_to_supervisor(report: str) -> bool:
                    text = str(report).strip()
                    if not text:
                        return False
                    self.mcp_tools.report_to_supervisor(
                        agent_id=self.player.id,
                        report=text[:4000],
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

                @tool
                def report_to_supervisor(report: str) -> bool:
                    """슈퍼바이저에게 관찰·의심 정보를 짧게 보고한다. 남용하지 말 것."""
                    return _report_to_supervisor(report)

                tool_llm = llm.bind_tools([send_chat, submit_vote, use_ability, report_to_supervisor])
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
                        elif (
                            name == "report_to_supervisor"
                            and "report" in args
                            and phase
                            in (
                                Phase.DAY_CHAT,
                                Phase.DAY_VOTE,
                                Phase.FINAL_VOTE,
                                Phase.NIGHT_MAFIA,
                                Phase.NIGHT_ABILITY,
                            )
                        ):
                            if _report_to_supervisor(str(args["report"])):
                                executed_any = True
                    except Exception:
                        # 도구 실행 실패는 폴백으로 처리한다.
                        executed_any = False
                        break

                decision = self._decision_from_tool_calls(tool_calls=tool_calls, phase=phase)
                if decision is not None and executed_any:
                    return decision, True, rag_context

            structured_llm = llm.with_structured_output(AgentDecision)
            messages = [SystemMessage(content=structured_system_prompt), HumanMessage(content=str(human_prompt))]
            decision = await asyncio.to_thread(structured_llm.invoke, messages)
            return decision, False, rag_context
        except Exception:
            return fallback(), False, rag_context

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
