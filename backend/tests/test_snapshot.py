from __future__ import annotations

from backend.game.snapshot import ui_phase
from backend.models.game import Phase


def test_ui_phase_final_speech() -> None:
    assert ui_phase(Phase.FINAL_SPEECH) == "final_speech"


def test_ui_phase_final_vote() -> None:
    assert ui_phase(Phase.FINAL_VOTE) == "final_vote"

