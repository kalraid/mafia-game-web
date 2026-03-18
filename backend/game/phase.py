from __future__ import annotations

from dataclasses import dataclass

from backend.models.game import Phase


@dataclass
class PhaseConfig:
    duration_seconds: int


PHASE_SEQUENCE: list[Phase] = [
    Phase.DAY_CHAT,
    Phase.DAY_VOTE,
    Phase.FINAL_SPEECH,
    Phase.FINAL_VOTE,
    Phase.NIGHT_MAFIA,
    Phase.NIGHT_ABILITY,
    Phase.NIGHT_RESULT,
]


PHASE_DURATIONS: dict[Phase, PhaseConfig] = {
    Phase.DAY_CHAT: PhaseConfig(duration_seconds=180),
    Phase.DAY_VOTE: PhaseConfig(duration_seconds=60),
    Phase.FINAL_SPEECH: PhaseConfig(duration_seconds=30),
    Phase.FINAL_VOTE: PhaseConfig(duration_seconds=30),
    Phase.NIGHT_MAFIA: PhaseConfig(duration_seconds=90),
    Phase.NIGHT_ABILITY: PhaseConfig(duration_seconds=60),
    Phase.NIGHT_RESULT: PhaseConfig(duration_seconds=10),
}


def get_next_phase(current: Phase) -> Phase:
    try:
        idx = PHASE_SEQUENCE.index(current)
    except ValueError:
        return Phase.DAY_CHAT
    return PHASE_SEQUENCE[(idx + 1) % len(PHASE_SEQUENCE)]


def get_phase_duration(phase: Phase) -> int:
    return PHASE_DURATIONS[phase].duration_seconds
