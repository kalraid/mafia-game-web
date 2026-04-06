from __future__ import annotations

from backend.game.engine import GameEngine
from backend.game.snapshot import build_game_state_payload, ui_phase
from backend.models.game import GameState, Phase, Player, Role, Team


def test_ui_phase_final_speech() -> None:
    assert ui_phase(Phase.FINAL_SPEECH) == "final_speech"


def test_ui_phase_final_vote() -> None:
    assert ui_phase(Phase.FINAL_VOTE) == "final_vote"


def test_build_game_state_payload_includes_rag_context() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=30,
        players=[
            Player(
                id="a",
                name="A",
                role=Role.CITIZEN,
                team=Team.CITIZEN,
                is_alive=True,
            ),
        ],
    )
    engine = GameEngine(state)
    rag = [{"text": "snippet", "score": 0.2, "metadata": {"title": "t"}}]
    payload = build_game_state_payload(engine, rag_context=rag)
    assert payload.get("rag_context") == rag


def test_build_game_state_payload_omits_empty_rag_context() -> None:
    state = GameState(
        game_id="g2",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=30,
        players=[
            Player(
                id="a",
                name="A",
                role=Role.CITIZEN,
                team=Team.CITIZEN,
                is_alive=True,
            ),
        ],
    )
    engine = GameEngine(state)
    payload = build_game_state_payload(engine, rag_context=[])
    assert "rag_context" not in payload

