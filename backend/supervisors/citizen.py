from __future__ import annotations

from typing import List

from backend.models.directive import Directive, Report
from backend.models.game import GameState


class CitizenSupervisor:
    def __init__(self, supervisor_id: str = "citizen_supervisor") -> None:
        self.supervisor_id = supervisor_id

    def issue_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
        """
        Phase 4 스켈레톤: 간단히 의심 대상 1명을 정해 시민 에이전트에게 집중 추궁 지시를 내리는 형태.
        실제 trust_score 기반 전략은 이후 단계에서 구현.
        """
        alive_ai_players = [p for p in state.players if not p.is_human and p.is_alive]
        if not alive_ai_players:
            return []

        suspect = alive_ai_players[0]
        directives: List[Directive] = []
        for player in alive_ai_players:
            directives.append(
                Directive(
                    target_agent=player.id,
                    from_=self.supervisor_id,
                    type="speech_strategy",
                    content=f"{suspect.name}을(를) 집중적으로 의심하는 발언을 해라.",
                    priority="medium",
                    round=state.round,
                )
            )
        return directives
