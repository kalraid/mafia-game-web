from __future__ import annotations

import asyncio
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.agents.persona import AgentPersona
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
    def __init__(self, agent_id: str, persona: AgentPersona, player: Player) -> None:
        self.agent_id = agent_id
        self.persona = persona
        self.player = player

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        # Phase 2 핵심: LLM 연동(키가 없으면 안전 폴백)
        decision = await self._decide_with_llm(agent_input)

        return AgentOutput(
            speech=decision.speech,
            action=(
                {"type": decision.ability, "target": decision.ability_target}
                if decision.ability is not None
                else None
            ),
            vote=decision.vote_target,
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
            if phase == Phase.DAY_VOTE:
                target = random.choice(alive_ids) if alive_ids else None
                return AgentDecision(
                    vote_target=target,
                    reasoning="fallback: random vote target",
                    confidence=0.0,
                )
            if phase == Phase.NIGHT_ABILITY:
                ability = self._allowed_ability_for_role(self.player.role)[0]
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

        phase_instruction = ""
        if phase == Phase.DAY_CHAT:
            phase_instruction = (
                "현재 Phase는 낮 채팅이다. speech만 작성하고 vote/ability 필드는 null로 둬라."
            )
        elif phase == Phase.DAY_VOTE:
            phase_instruction = "현재 Phase는 낮 투표이다. alive한 player_id 중 vote_target을 선택해라."
        elif phase == Phase.NIGHT_ABILITY:
            allowed = self._allowed_ability_for_role(self.player.role)
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
        if role in (Role.JESTER, Role.SPY, Role.CITIZEN):
            return ["investigate"]
        return ["investigate"]
