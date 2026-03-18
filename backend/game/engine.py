from __future__ import annotations

from typing import Dict

from backend.game.phase import get_next_phase, get_phase_duration
from backend.game.win_condition import check_winner
from backend.models.game import GameState, Phase


class GameEngine:
    def __init__(self, state: GameState) -> None:
        self.state = state
        self.votes: Dict[str, str] = {}

    def start(self) -> None:
        self.state.phase = Phase.DAY_CHAT
        self.state.timer_seconds = get_phase_duration(self.state.phase)

    def advance_phase(self) -> None:
        winner = check_winner(self.state)
        if winner:
            self.state.winner = winner
            return

        self.state.phase = get_next_phase(self.state.phase)
        self.state.timer_seconds = get_phase_duration(self.state.phase)
        if self.state.phase == Phase.DAY_CHAT:
            self.state.round += 1
