from __future__ import annotations

from typing import List

from backend.models.directive import Directive, Report
from backend.models.game import GameState, Role


class NeutralSupervisor:
    def __init__(self, supervisor_id: str = "neutral_supervisor") -> None:
        self.supervisor_id = supervisor_id

    def issue_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
        directives: List[Directive] = []

        for p in state.players:
            if not p.is_alive:
                continue

            if p.role == Role.JESTER:
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="speech_strategy",
                        content="의심을 살 만한 행동을 하되, 너무 노골적이지 않게 스스로를 방어하라.",
                        priority="medium",
                        round=state.round,
                    )
                )
            elif p.role == Role.SPY:
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="speech_strategy",
                        content="너무 튀지 않게, 정보를 모으면서 조용히 생존을 우선해라.",
                        priority="medium",
                        round=state.round,
                    )
                )

        return directives
