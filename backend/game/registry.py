from __future__ import annotations

from typing import Dict

from backend.game.engine import GameEngine
from backend.game.phase import get_phase_duration
from backend.models.game import GameState, Phase, Player, Role, Team


class GameRegistry:
    """
    game_id -> GameEngine 매핑 (In-Memory, 단일 서버 개발용).
    """

    def __init__(self) -> None:
        self._games: Dict[str, GameEngine] = {}

    def get_or_create(self, game_id: str) -> GameEngine:
        if game_id in self._games:
            return self._games[game_id]

        state = GameState(
            game_id=game_id,
            phase=Phase.DAY_CHAT,
            round=1,
            timer_seconds=get_phase_duration(Phase.DAY_CHAT),
            players=[
                Player(
                    id="나",
                    name="나",
                    role=Role.CITIZEN,
                    team=Team.CITIZEN,
                    is_alive=True,
                    is_human=True,
                    trust_score=0.5,
                ),
                Player(
                    id="김민준",
                    name="김민준",
                    role=Role.MAFIA,
                    team=Team.MAFIA,
                    is_alive=True,
                    is_human=False,
                    trust_score=0.5,
                ),
                Player(
                    id="박서연",
                    name="박서연",
                    role=Role.DETECTIVE,
                    team=Team.CITIZEN,
                    is_alive=True,
                    is_human=False,
                    trust_score=0.5,
                ),
                Player(
                    id="최수아",
                    name="최수아",
                    role=Role.DOCTOR,
                    team=Team.CITIZEN,
                    is_alive=True,
                    is_human=False,
                    trust_score=0.5,
                ),
                Player(
                    id="이지호",
                    name="이지호",
                    role=Role.CITIZEN,
                    team=Team.CITIZEN,
                    is_alive=True,
                    is_human=False,
                    trust_score=0.5,
                ),
            ],
        )
        engine = GameEngine(state)
        engine.start()
        self._games[game_id] = engine
        return engine

    def get(self, game_id: str) -> GameEngine | None:
        return self._games.get(game_id)
