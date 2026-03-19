from __future__ import annotations

from typing import Dict

from backend.game.engine import GameEngine
from backend.game.phase import get_phase_duration
from backend.models.game import GameState, Phase


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
            players=[],
        )
        engine = GameEngine(state)
        engine.start()
        self._games[game_id] = engine
        return engine

    def get(self, game_id: str) -> GameEngine | None:
        return self._games.get(game_id)
