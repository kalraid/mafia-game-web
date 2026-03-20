from __future__ import annotations

from typing import Dict

from backend.game.phase import get_next_phase, get_phase_duration
from backend.game.vote import tally_votes
from backend.game.win_condition import check_winner
from backend.models.game import GameEvent, GameState, Phase
from backend.game.roles import ROLE_ABILITIES, RoleAbilityContext


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

            players_by_id = {p.id: p for p in self.state.players}

            # 의사 보호(protected)는 NIGHT_ABILITY 종료 후 해제한다.
            protected_targets: list[str] = []

            # 1) 보호/조사 먼저 처리 (heal -> investigate)
            for actor_id, req in self.ability_requests.items():
                ability = req.get("ability")
                target_id = req.get("target_id")
                if not ability or not target_id:
                    continue

                actor = players_by_id.get(actor_id)
                target = players_by_id.get(target_id)
                if actor is None or target is None:
                    continue

                # heal: doctor protect
                if ability == "heal":
                    handler = ROLE_ABILITIES.get(actor.role)
                    if handler is not None:
                        handler(RoleAbilityContext(game_state=self.state, actor=actor, target=target))
                        protected_targets.append(target.id)

                # investigate: detective/fortune_teller 조사
                if ability == "investigate":
                    handler = ROLE_ABILITIES.get(actor.role)
                    if handler is not None:
                        handler(RoleAbilityContext(game_state=self.state, actor=actor, target=target))

            # 2) 공격은 최종 1명 처치 (MVP: 첫 번째 attack 요청만 적용)
            first_attack: tuple[str, dict] | None = None
            for actor_id, req in self.ability_requests.items():
                if req.get("ability") == "attack" and req.get("target_id"):
                    first_attack = (actor_id, req)
                    break

            if first_attack is not None:
                actor_id, req = first_attack
                actor = players_by_id.get(actor_id)
                target_id = req.get("target_id")
                target = players_by_id.get(target_id) if isinstance(target_id, str) else None
                if actor is not None and target is not None:
                    handler = ROLE_ABILITIES.get(actor.role)
                    if handler is not None:
                        handler(RoleAbilityContext(game_state=self.state, actor=actor, target=target))

            # 3) protected 플래그 해제
            for pid in protected_targets:
                p = players_by_id.get(pid)
                if p is not None:
                    p.ability_used = False

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
