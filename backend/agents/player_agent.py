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

    def __init__(self, agent_id: str, persona: AgentPersona, player: Player) -> None:
        self.agent_id = agent_id
        self.persona = persona
        self.player = player

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
            knowledge_dir = os.getenv("RAG_KNOWLEDGE_DIR", "./backend/rag/knowledge")
            store.index_from_disk(knowledge_root=knowledge_dir)
            PlayerAgent._rag_retriever = StrategyRetriever(store=store)
            return PlayerAgent._rag_retriever
        except Exception:
            return None

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        # Phase 2 핵심: LLM 연동(키가 없으면 안전 폴백)
        decision = await self._decide_with_llm(agent_input)

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

        return AgentOutput(
            speech=speech,
            action=(
                {"type": ability, "target": ability_target}
                if ability is not None and ability_target is not None
                else None
            ),
            vote=vote_target,
            internal_notes=decision.reasoning,
        )

    async def _decide_with_llm(self, agent_input: AgentInput) -> AgentDecision:
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
            return fallback()

        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return fallback()

        # Lazy import to avoid hard failure when env doesn't have optional deps
        try:
            from langchain_anthropic import ChatAnthropic
            from langchain_core.messages import SystemMessage, HumanMessage
        except Exception:
            return fallback()

        try:
            model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4")
            llm = ChatAnthropic(model=model_name, temperature=0, api_key=api_key)
        except Exception:
            return fallback()

        # Phase별 간단한 출력 스키마 유도
        system_prompt = (
            "너는 AI 마피아 게임 에이전트다. 아래 지시에 따라 반드시 JSON 스키마로만 답한다."
            " 말투는 persona의 speech_style을 따른다."
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

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=str(human_prompt))]

        try:
            structured_llm = llm.with_structured_output(AgentDecision)
            # with_structured_output은 sync 호출이므로 async에서 to_thread로 감싼다.
            decision: AgentDecision = await asyncio.to_thread(structured_llm.invoke, messages)
            return decision
        except Exception:
            return fallback()

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
