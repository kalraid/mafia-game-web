from __future__ import annotations

from collections import Counter
from typing import Any, Dict

from backend.game.engine import GameEngine
from backend.models.game import Phase, Player, Role


def role_to_korean(role: Role) -> str:
    return {
        Role.CITIZEN: "시민",
        Role.DETECTIVE: "경찰",
        Role.DOCTOR: "의사",
        Role.FORTUNE_TELLER: "점쟁이",
        Role.MAFIA: "마피아",
        Role.KILLER: "킬러",
        Role.JESTER: "광대",
        Role.SPY: "스파이",
    }.get(role, role.value)


def ui_phase(phase: Phase) -> str:
    if phase == Phase.DAY_CHAT:
        return "day_chat"
    if phase == Phase.DAY_VOTE:
        return "day_vote"
    if phase == Phase.FINAL_SPEECH:
        return "final_speech"
    if phase == Phase.FINAL_VOTE:
        return "final_vote"
    if phase in (Phase.NIGHT_MAFIA, Phase.NIGHT_ABILITY):
        return "night"
    if phase == Phase.NIGHT_RESULT:
        return "result"
    return "day_chat"


def _votes_count(votes: Dict[str, str]) -> Counter[str]:
    # voter_id -> target_id
    return Counter(votes.values())


def build_game_state_payload(
    engine: GameEngine,
    *,
    death_info: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    프론트엔드(status_panel/result 페이지)가 바로 consume할 payload를 생성합니다.
    """
    death_info = death_info or {}
    votes_counter = _votes_count(engine.get_vote_snapshot())

    players = []
    for p in engine.state.players:
        votes = int(votes_counter.get(p.id, 0))

        player_dict: Dict[str, Any] = {
            "name": p.name,
            "is_alive": p.is_alive,
            "role": role_to_korean(p.role),
            "votes": votes,
            "is_silent": False,
            # 프론트 result 페이지용 확장 필드
            "death_round": death_info.get(p.id, {}).get("death_round", ""),
            "death_cause": death_info.get(p.id, {}).get("death_cause", ""),
        }
        players.append(player_dict)

    return {
        "players": players,
        "phase": ui_phase(engine.state.phase),
        "round": engine.state.round,
        "timer_seconds": engine.state.timer_seconds,
        "winner": engine.state.winner,
    }

