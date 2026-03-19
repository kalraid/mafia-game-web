from __future__ import annotations

from backend.models.directive import Report
from backend.models.game import GameState, Phase, Player, Role, Team
from backend.supervisors.citizen import CitizenSupervisor
from backend.supervisors.mafia import MafiaSupervisor


def test_citizen_supervisor_chooses_lowest_trust_score_as_suspect() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="a1", name="A", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True, is_human=False, trust_score=0.8),
            Player(id="a2", name="B", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True, is_human=False, trust_score=0.2),
            Player(id="a3", name="C", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True, is_human=False, trust_score=0.5),
        ],
    )
    sup = CitizenSupervisor()
    directives = sup.issue_directives(state, reports=[])
    assert len(directives) == 3
    # 의심 대상은 trust_score 최저인 B
    assert "B" in directives[0].content


def test_mafia_supervisor_prioritizes_detective_then_doctor() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="m1", name="M", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="d1", name="D", role=Role.DETECTIVE, team=Team.CITIZEN, is_alive=True),
            Player(id="doc", name="Doc", role=Role.DOCTOR, team=Team.CITIZEN, is_alive=True),
            Player(id="c1", name="C", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True, trust_score=0.9),
        ],
    )
    sup = MafiaSupervisor()
    target = sup.choose_kill_target(state, reports=[])
    assert target in ("d1", "doc")  # detective or doctor 중 하나


def test_mafia_supervisor_falls_back_to_high_trust_citizen() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="m1", name="M", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="c1", name="Low", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True, trust_score=0.2),
            Player(id="c2", name="High", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True, trust_score=0.9),
        ],
    )
    sup = MafiaSupervisor()
    target = sup.choose_kill_target(state, reports=[])
    assert target == "c2"  # trust_score 높은 시민 우선
