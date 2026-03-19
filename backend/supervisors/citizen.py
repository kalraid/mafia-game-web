from __future__ import annotations

from typing import List

from backend.models.directive import Directive, Report
from backend.models.game import GameState


class CitizenSupervisor:
    def __init__(self, supervisor_id: str = "citizen_supervisor") -> None:
        self.supervisor_id = supervisor_id

    def _choose_suspect(self, state: GameState, reports: List[Report]) -> str | None:
        """
        의심 대상: reports에 '마피아' 등으로 언급된 플레이어 우선, 없으면 trust_score 가장 낮은 AI.
        """
        alive_ai = [p for p in state.players if not p.is_human and p.is_alive]
        if not alive_ai:
            return None

        # reports에서 "X는 마피아" / "mafia" 등으로 지목된 player id 수집
        reported_suspects: List[str] = []
        for r in reports:
            content_lower = (r.content or "").lower()
            if "mafia" in content_lower or "마피아" in r.content:
                # player id 패턴: 영문/한글 ID 추출 (간단히 단어 나열 가정)
                for p in alive_ai:
                    if p.id in r.content or p.name in r.content:
                        reported_suspects.append(p.id)
                        break

        if reported_suspects:
            return reported_suspects[0]

        # trust_score 가장 낮은 플레이어를 의심 대상
        suspect = min(alive_ai, key=lambda p: p.trust_score)
        return suspect.id

    def issue_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
        """
        trust_score 기반 의심 대상 선정 + reports 반영.
        """
        alive_ai_players = [p for p in state.players if not p.is_human and p.is_alive]
        if not alive_ai_players:
            return []

        suspect_id = self._choose_suspect(state, reports)
        suspect_name = next((p.name for p in state.players if p.id == suspect_id), suspect_id or "한 명")
        directives: List[Directive] = []
        for player in alive_ai_players:
            directives.append(
                Directive(
                    target_agent=player.id,
                    from_=self.supervisor_id,
                    type="speech_strategy",
                    content=f"{suspect_name}을(를) 집중적으로 의심하는 발언을 해라.",
                    priority="medium",
                    round=state.round,
                )
            )
        return directives

    def issue_night_ability_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
        """
        밤 능력(Ability) 단계용 A2A 지시 스켈레톤.
        """
        alive_players = [p for p in state.players if p.is_alive]
        mafia_players = [p for p in alive_players if p.team.value == "mafia"]
        citizen_players = [p for p in alive_players if p.team.value != "mafia"]

        first_mafia = mafia_players[0].id if mafia_players else (citizen_players[0].id if citizen_players else None)

        directives: List[Directive] = []
        for p in alive_players:
            if p.team.value == "mafia":
                continue

            if p.role.value == "detective":
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="ability_strategy",
                        content=f"밤에는 조사(investigate)를 사용해. 대상은 {first_mafia}를 확인하라.",
                        priority="high",
                        round=state.round,
                    )
                )
            elif p.role.value == "doctor":
                heal_target = citizen_players[0].id if citizen_players else p.id
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="ability_strategy",
                        content=f"밤에는 보호(heal)를 사용해. 대상은 {heal_target}로 하라.",
                        priority="high",
                        round=state.round,
                    )
                )
            else:
                # 시민/중립 중 밤 능력이 있는 역할은 후속 단계에서 세부 처리
                directives.append(
                    Directive(
                        target_agent=p.id,
                        from_=self.supervisor_id,
                        type="ability_strategy",
                        content="밤에는 역할에 맞는 능력을 사용하거나 필요 없으면 null로 두고 생존 중심으로 행동하라.",
                        priority="medium",
                        round=state.round,
                    )
                )

        return directives
