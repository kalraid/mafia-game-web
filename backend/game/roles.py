from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from backend.models.directive import Report
from backend.models.game import GameEvent, GameState, Player, Role


@dataclass
class RoleAbilityContext:
    game_state: GameState
    actor: Player
    target: Optional[Player]


AbilityHandler = Callable[[RoleAbilityContext], GameState]


def detective_investigate(ctx: RoleAbilityContext) -> GameState:
    """
    조사 결과를 state.reports에 기록한다.
    """
    if ctx.target is None:
        return ctx.game_state

    result = f"{ctx.target.name}은(는) {ctx.target.team.value} 계열입니다."
    ctx.game_state.reports.append(
        Report(
            agent_id=ctx.actor.id,
            content=result,
            round=ctx.game_state.round,
        )
    )
    return ctx.game_state


def doctor_protect(ctx: RoleAbilityContext) -> GameState:
    """
    의사는 대상에게 protected 상태를 임시 부여한다.
    protected 상태는 engine에서 NIGHT_ABILITY 종료 후 해제한다.
    """
    if ctx.target is None:
        return ctx.game_state

    ctx.target.ability_used = True
    return ctx.game_state


def mafia_attack(ctx: RoleAbilityContext) -> GameState:
    """
    마피아 공격은 protected(=ability_used=True)이면 무효화된다.
    """
    if ctx.target is None:
        return ctx.game_state

    if ctx.target.ability_used:
        return ctx.game_state

    ctx.target.is_alive = False
    ctx.game_state.events.append(
        GameEvent(
            type="player_death",
            payload={
                "player": ctx.target.id,
                "role": ctx.target.role.value,
                "cause": "night_attack",
                "round": ctx.game_state.round,
            },
        )
    )
    return ctx.game_state


def killer_piercing_attack(ctx: RoleAbilityContext) -> GameState:
    """
    킬러 관통은 의사의 보호(protected)를 무시한다.
    관통은 actor(킬러) 기준 1회만 허용한다.
    """
    if ctx.target is None:
        return ctx.game_state

    # 이미 관통을 사용한 경우
    if ctx.actor.ability_used:
        return ctx.game_state

    ctx.target.is_alive = False
    ctx.actor.ability_used = True
    ctx.game_state.events.append(
        GameEvent(
            type="player_death",
            payload={
                "player": ctx.target.id,
                "role": ctx.target.role.value,
                "cause": "night_attack",
                "round": ctx.game_state.round,
            },
        )
    )
    return ctx.game_state


def fortune_teller_divine(ctx: RoleAbilityContext) -> GameState:
    """
    점쟁이: 대상의 팀(마피아/시민)을 추정해 보고서로 남긴다.
    (현재 MVP에서는 경찰/점쟁이의 공개 범위 차이를 UI 단계에서 분리하지 않음)
    """
    if ctx.target is None:
        return ctx.game_state

    result = f"{ctx.target.name}은(는) {ctx.target.team.value}입니다. (점술 결과 — 비공개)"
    ctx.game_state.reports.append(
        Report(
            agent_id=ctx.actor.id,
            content=result,
            round=ctx.game_state.round,
        )
    )
    return ctx.game_state


def spy_eavesdrop(ctx: RoleAbilityContext) -> GameState:
    """
    스파이: 현재까지 쌓인 `mafia_secret` 채팅 내용을 요약해 보고서로 남긴다.
    (ChatMessage에 round 필드가 없어, 현 시점까지의 mafia_secret을 사용)
    """
    mafia_chats = [m for m in ctx.game_state.chat_history if getattr(m, "channel", None) == "mafia_secret"]
    summary = " | ".join(m.content for m in mafia_chats) if mafia_chats else "마피아 채팅 없음"

    ctx.game_state.reports.append(
        Report(
            agent_id=ctx.actor.id,
            content=f"[스파이 도청] {summary}",
            round=ctx.game_state.round,
        )
    )
    return ctx.game_state


ROLE_ABILITIES: dict[Role, AbilityHandler] = {
    Role.DETECTIVE: detective_investigate,
    Role.FORTUNE_TELLER: fortune_teller_divine,
    Role.DOCTOR: doctor_protect,
    Role.MAFIA: mafia_attack,
    Role.KILLER: killer_piercing_attack,
    Role.SPY: spy_eavesdrop,
}
