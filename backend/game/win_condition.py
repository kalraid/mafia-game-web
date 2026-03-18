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

    if any(p.role == Role.JESTER and not p.is_alive for p in state.players):
        return "jester"

    if mafia_count == 0:
        return "citizen"

    if mafia_count >= citizen_like_count:
        return "mafia"

    return None
