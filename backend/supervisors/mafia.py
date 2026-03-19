from __future__ import annotations

import random
from typing import List

from backend.models.directive import Directive, Report
from backend.models.game import GameState, Team, Role


class MafiaSupervisor:
    def __init__(self, supervisor_id: str = "mafia_supervisor") -> None:
        self.supervisor_id = supervisor_id

    def choose_kill_target(self, state: GameState, reports: List[Report]) -> str | None:
        """
        AGENT_DESIGN 우선순위: 1) 경찰(detective), 2) 의사(doctor), 3) trust_score 높은 시민, 4) 무작위.
        """
        candidates = [p for p in state.players if p.is_alive and p.team != Team.MAFIA]
        if not candidates:
            return None

        # 1순위: detective
        detectives = [p for p in candidates if p.role == Role.DETECTIVE]
        if detectives:
            return random.choice(detectives).id
        # 2순위: doctor
        doctors = [p for p in candidates if p.role == Role.DOCTOR]
        if doctors:
            return random.choice(doctors).id
        # 3순위: trust_score 높은 시민 (영향력 큰 시민)
        candidates_sorted = sorted(candidates, key=lambda p: -p.trust_score)
        return candidates_sorted[0].id

    def issue_concealment_directives(self, state: GameState) -> List[Directive]:
        """
        낮 Phase 은폐 전략 지시 스켈레톤.
        """
        mafia_players = [p for p in state.players if p.team == Team.MAFIA and p.is_alive]
        directives: List[Directive] = []
        for mafia in mafia_players:
            directives.append(
                Directive(
                    target_agent=mafia.id,
                    from_=self.supervisor_id,
                    type="speech_strategy",
                    content="시민인 것처럼 자연스럽게 행동하되, 다른 사람에게 의심을 돌려라.",
                    priority="medium",
                    round=state.round,
                )
            )
        return directives

    def issue_night_ability_directives(self, state: GameState) -> List[Directive]:
        """
        밤 능력 단계용 A2A 지시 스켈레톤.
        - 마피아는 최종 1명 대상(choose_kill_target)에게 공격(attack) 지시
        """
        kill_target = self.choose_kill_target(state=state, reports=[])
        if not kill_target:
            return []

        mafia_players = [p for p in state.players if p.is_alive and p.team == Team.MAFIA]
        directives: List[Directive] = []
        for mafia in mafia_players:
            directives.append(
                Directive(
                    target_agent=mafia.id,
                    from_=self.supervisor_id,
                    type="ability_strategy",
                    content=f"밤에는 공격(attack)을 사용해. 처치 대상은 {kill_target}로 하라.",
                    priority="high",
                    round=state.round,
                )
            )
        return directives
