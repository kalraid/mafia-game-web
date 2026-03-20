from __future__ import annotations

from datetime import datetime

from backend.game.engine import GameEngine
from backend.game.vote import tally_votes
from backend.game.phase import get_phase_duration
from backend.game.win_condition import check_winner
from backend.models.chat import ChatMessage
from backend.models.game import GameEvent, GameState, Phase, Player, Role, Team


def test_tally_votes_basic() -> None:
    votes = {"a": "x", "b": "x", "c": "y"}
    target, tied = tally_votes(votes)
    assert target == "x"
    assert tied is False


def test_tally_votes_tie() -> None:
    votes = {"a": "x", "b": "y", "c": "y", "d": "x"}
    target, tied = tally_votes(votes)
    assert target is None
    assert tied is True


def test_game_engine_submit_snapshots() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=get_phase_duration(Phase.DAY_CHAT),
        players=[
            Player(id="p1", name="A", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
            Player(id="p2", name="B", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        ],
    )
    engine = GameEngine(state)
    engine.start()

    engine.submit_vote(voter_id="p1", target_id="p2")
    engine.submit_ability(agent_id="p2", ability="attack", target_id="p1")

    assert engine.get_vote_snapshot()["p1"] == "p2"
    assert engine.get_ability_snapshot()["p2"]["ability"] == "attack"


def test_check_winner_citizen_when_no_mafia() -> None:
    state = GameState(
        game_id="g2",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="p1", name="A", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
            Player(id="p2", name="B", role=Role.DOCTOR, team=Team.CITIZEN, is_alive=True),
        ],
    )
    assert check_winner(state) == "citizen"


def test_check_winner_mafia_when_mafia_ge_citizen_like() -> None:
    state = GameState(
        game_id="g3",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="m1", name="M1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="m2", name="M2", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="c1", name="C1", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
        ],
    )
    assert check_winner(state) == "mafia"


def test_check_winner_jester_when_jester_is_dead() -> None:
    state = GameState(
        game_id="g4",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="j1", name="J1", role=Role.JESTER, team=Team.NEUTRAL, is_alive=False),
            Player(id="c1", name="C1", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
            Player(id="m1", name="M1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        ],
        events=[
            GameEvent(
                type="player_death",
                payload={"player": "j1", "role": "jester", "cause": "vote"},
            )
        ],
    )
    assert check_winner(state) == "jester"


def test_engine_day_vote_kills_and_sets_winner() -> None:
    state = GameState(
        game_id="g5",
        phase=Phase.DAY_VOTE,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="m1", name="M1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="c1", name="C1", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
        ],
    )
    engine = GameEngine(state)

    engine.submit_vote(voter_id="m1", target_id="c1")
    engine.advance_phase()

    assert state.players[1].is_alive is False
    assert state.winner == "mafia"
    assert any(e.type == "player_death" and e.payload.get("cause") == "vote" for e in state.events)


def test_engine_first_night_has_no_mafia_attack() -> None:
    state = GameState(
        game_id="g6",
        phase=Phase.NIGHT_ABILITY,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="m1", name="M1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="c1", name="C1", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
        ],
    )
    engine = GameEngine(state)

    engine.submit_ability(agent_id="m1", ability="attack", target_id="c1")
    engine.advance_phase()

    assert state.players[1].is_alive is True


def test_engine_night_ability_heal_cancels_attack() -> None:
    state = GameState(
        game_id="g7",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="m1", name="M1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
            Player(id="d1", name="D1", role=Role.DOCTOR, team=Team.CITIZEN, is_alive=True),
            Player(id="c1", name="C1", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
        ],
    )
    engine = GameEngine(state)

    engine.submit_ability(agent_id="m1", ability="attack", target_id="c1")
    engine.submit_ability(agent_id="d1", ability="heal", target_id="c1")
    engine.advance_phase()

    assert state.players[2].is_alive is True


def test_engine_night_ability_killer_piercing_ignores_protection() -> None:
    state = GameState(
        game_id="g7b",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="k1", name="Killer", role=Role.KILLER, team=Team.MAFIA, is_alive=True),
            Player(id="d1", name="Doctor", role=Role.DOCTOR, team=Team.CITIZEN, is_alive=True),
            Player(id="c1", name="Citizen", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
        ],
    )
    engine = GameEngine(state)

    # killer attack + doctor heal on the same target
    engine.submit_ability(agent_id="k1", ability="attack", target_id="c1")
    engine.submit_ability(agent_id="d1", ability="heal", target_id="c1")
    engine.advance_phase()

    assert state.players[2].is_alive is False


def test_engine_night_ability_detective_investigate_writes_report() -> None:
    state = GameState(
        game_id="g7c",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="det", name="Detective", role=Role.DETECTIVE, team=Team.CITIZEN, is_alive=True),
            Player(id="m1", name="Mafia1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        ],
    )
    engine = GameEngine(state)
    engine.submit_ability(agent_id="det", ability="investigate", target_id="m1")
    engine.advance_phase()

    assert any("Mafia1" in r.content and "mafia" in r.content.lower() for r in state.reports)


def test_engine_night_ability_fortune_teller_investigate_writes_report() -> None:
    state = GameState(
        game_id="g7ca",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="ft", name="Fortune", role=Role.FORTUNE_TELLER, team=Team.CITIZEN, is_alive=True),
            Player(id="m1", name="Mafia1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        ],
    )
    engine = GameEngine(state)
    engine.submit_ability(agent_id="ft", ability="investigate", target_id="m1")
    engine.advance_phase()

    assert any("Mafia1" in r.content and "mafia" in r.content.lower() for r in state.reports)


def test_engine_night_ability_spy_listen_records_report() -> None:
    state = GameState(
        game_id="g7cb",
        phase=Phase.NIGHT_ABILITY,
        round=2,
        timer_seconds=60,
        players=[
            Player(id="s1", name="Spy", role=Role.SPY, team=Team.NEUTRAL, is_alive=True),
            Player(id="m1", name="Mafia1", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        ],
        chat_history=[
            ChatMessage(
                id="chat_1",
                sender="m1",
                content="secret hello",
                channel="mafia_secret",
                timestamp=datetime.utcnow(),
                is_ai=True,
            )
        ],
    )
    engine = GameEngine(state)
    engine.submit_ability(agent_id="s1", ability="spy_listen", target_id="m1")
    engine.advance_phase()

    assert any("[스파이 도청]" in r.content and "secret hello" in r.content for r in state.reports)


def test_check_winner_does_not_declare_jester_when_jester_dies_at_night() -> None:
    state = GameState(
        game_id="g8",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="j1", name="J1", role=Role.JESTER, team=Team.NEUTRAL, is_alive=False),
            Player(id="c1", name="C1", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
        ],
        events=[
            GameEvent(
                type="player_death",
                payload={"player": "j1", "role": "jester", "cause": "ability"},
            )
        ],
    )
    assert check_winner(state) == "citizen"

