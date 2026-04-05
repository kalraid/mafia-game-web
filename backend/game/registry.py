from __future__ import annotations

from typing import Dict

from backend.game.composition import build_initial_players
from backend.game.engine import GameEngine
from backend.game.phase import get_phase_duration
from backend.models.game import GameState, Phase


class GameRegistry:
    """
    game_id -> GameEngine 매핑 (In-Memory, 단일 서버 개발용).
    게임은 POST /game/create 로만 등록한다 (get_or_create 자동 생성 없음).
    """

    def __init__(self) -> None:
        self._games: Dict[str, GameEngine] = {}

    def get(self, game_id: str) -> GameEngine | None:
        return self._games.get(game_id)

    def create_game(self, game_id: str, host_name: str, player_count: int) -> GameEngine:
        if game_id in self._games:
            raise ValueError(f"game_id 이미 존재: {game_id}")

        players = build_initial_players(player_count, host_name)
        state = GameState(
            game_id=game_id,
            phase=Phase.DAY_CHAT,
            round=1,
            timer_seconds=get_phase_duration(Phase.DAY_CHAT),
            players=players,
        )
        engine = GameEngine(state)
        engine.start()
        self._games[game_id] = engine
        return engine
