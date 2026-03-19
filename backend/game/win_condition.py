from __future__ import annotations

from typing import Optional

from backend.models.game import GameState, Team, Role


def check_winner(state: GameState) -> Optional[str]:
    alive_players = [p for p in state.players if p.is_alive]

    mafia_count = sum(1 for p in alive_players if p.team == Team.MAFIA)
    citizen_like_count = sum(
        1
        for p in alive_players
        if p.team == Team.CITIZEN or p.role in (Role.JESTER, Role.SPY)
    )

    # 광대(Jester)는 "투표로 처형당했을 때" 단독 승리.
    # 밤에 사망하면 패배이므로, 사망 원인(cause)로 구분한다.
    for p in state.players:
        if p.role != Role.JESTER or p.is_alive:
            continue
        for e in state.events:
            if e.type != "player_death":
                continue
            if e.payload.get("player") != p.id:
                continue
            if e.payload.get("cause") == "vote":
                return "jester"

    if mafia_count == 0:
        return "citizen"

    if mafia_count >= citizen_like_count:
        return "mafia"

    return None
