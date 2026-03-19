from __future__ import annotations

from typing import Dict

from backend.game.phase import get_next_phase, get_phase_duration
from backend.game.win_condition import check_winner
from backend.models.game import GameState, Phase


class GameEngine:
    def __init__(self, state: GameState) -> None:
        self.state = state
        self.votes: Dict[str, str] = {}
        # agent_id -> {"ability": str, "target_id": str}
        self.ability_requests: Dict[str, Dict[str, str]] = {}

    def start(self) -> None:
        self.state.phase = Phase.DAY_CHAT
        self.state.timer_seconds = get_phase_duration(self.state.phase)

    def submit_vote(self, voter_id: str, target_id: str) -> None:
        self.votes[voter_id] = target_id

    def submit_ability(self, agent_id: str, ability: str, target_id: str) -> None:
        self.ability_requests[agent_id] = {"ability": ability, "target_id": target_id}

    def get_vote_snapshot(self) -> Dict[str, str]:
        return dict(self.votes)

    def get_ability_snapshot(self) -> Dict[str, Dict[str, str]]:
        return dict(self.ability_requests)

    def advance_phase(self) -> None:
        winner = check_winner(self.state)
        if winner:
            self.state.winner = winner
            return

        self.state.phase = get_next_phase(self.state.phase)
        self.state.timer_seconds = get_phase_duration(self.state.phase)
        if self.state.phase == Phase.DAY_CHAT:
            self.state.round += 1
