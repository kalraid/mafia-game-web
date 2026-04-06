from __future__ import annotations

from typing import List

from backend.models.directive import Directive, Report
from backend.models.game import GameState, Role


class NeutralSupervisor:
    def __init__(self, supervisor_id: str = "neutral_supervisor") -> None:
        self.supervisor_id = supervisor_id

    def issue_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
        directives: List[Directive] = []
        heat_on_spy = any(
            ("스파이" in (r.content or "")) or ("spy" in (r.content or "").lower()) for r in reports
        )

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
                spy_extra = (
                    " 최근 보고에서 스파이 노출 위험이 언급됐다. 더욱 은밀히 행동해라."
                    if heat_on_spy
                    else ""
                )
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="speech_strategy",
                        content="너무 튀지 않게, 정보를 모으면서 조용히 생존을 우선해라." + spy_extra,
                        priority="medium",
                        round=state.round,
                    )
                )

        return directives

    def issue_night_ability_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
        """
        밤 능력 단계용 A2A 지시 스켈레톤.
        - Spy: 마피아 비밀 채널을 엿듣는(spy_listen) 방향 지시
        - Jester: 무능력(없음)으로 간주하고 생존/발언 전략만 유지
        """
        alive_players = [p for p in state.players if p.is_alive]
        mafia_alive = [p for p in alive_players if p.team.value == "mafia"]
        mafia_target = mafia_alive[0].id if mafia_alive else None

        directives: List[Directive] = []
        for p in alive_players:
            if p.role == Role.SPY:
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="ability_strategy",
                        content=(
                            f"밤에는 엿듣기(spy_listen)를 사용해. 대상 채널 힌트: {mafia_target if mafia_target else 'none'}"
                        ),
                        priority="high",
                        round=state.round,
                    )
                )
            elif p.role == Role.JESTER:
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="speech_strategy",
                        content="밤에는 능력이 없으니 무리한 행동을 피하고, 다음 낮을 위해 생존/발언 준비를 해라.",
                        priority="medium",
                        round=state.round,
                    )
                )

        return directives
