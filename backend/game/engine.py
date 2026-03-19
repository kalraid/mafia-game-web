from __future__ import annotations

from typing import Dict

from backend.game.phase import get_next_phase, get_phase_duration
from backend.game.vote import tally_votes
from backend.game.win_condition import check_winner
from backend.models.game import GameEvent, GameState, Phase


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
        # 현재 phase에서 발생해야 하는 부작용(처형/사망/승리조건) 먼저 반영
        self._apply_phase_effects()

        winner = check_winner(self.state)
        if winner:
            self.state.winner = winner
            return

        self.state.phase = get_next_phase(self.state.phase)
        self.state.timer_seconds = get_phase_duration(self.state.phase)
        if self.state.phase == Phase.DAY_CHAT:
            self.state.round += 1

    def _apply_phase_effects(self) -> None:
        """
        MVP 수준의 phase 효과 반영.
        - DAY_VOTE/FINAL_VOTE: tally_votes 기반으로 1명 처형 처리
        - NIGHT_ABILITY: attack 요청이 있으면 1명 처치 처리(doctor heal이 대상이면 무효화)
        """
        if self.state.phase in (Phase.DAY_VOTE, Phase.FINAL_VOTE):
            target_id, tied = tally_votes(self.votes)
            if target_id is not None and not tied:
                self._kill_player(target_id, cause="vote")
            self.votes = {}

        elif self.state.phase == Phase.NIGHT_ABILITY:
            # 1번째 밤은 첫날 밤 규칙: 마피아 공격 없음(탐색 밤)
            if self.state.round == 1:
                self.ability_requests = {}
                return

            attack_targets = [
                req.get("target_id")
                for req in self.ability_requests.values()
                if req.get("ability") == "attack" and req.get("target_id")
            ]
            heal_targets = {
                req.get("target_id")
                for req in self.ability_requests.values()
                if req.get("ability") == "heal" and req.get("target_id")
            }

            kill_target = attack_targets[0] if attack_targets else None
            if kill_target and kill_target not in heal_targets:
                self._kill_player(kill_target, cause="night_attack")

            self.ability_requests = {}

    def _kill_player(self, player_id: str, cause: str) -> None:
        player = next((p for p in self.state.players if p.id == player_id), None)
        if player is None or not player.is_alive:
            return
        player.is_alive = False

        self.state.events.append(
            GameEvent(
                type="player_death",
                payload={
                    "player": player.id,
                    "role": player.role.value,
                    "cause": cause,
                    "round": self.state.round,
                },
            )
        )
