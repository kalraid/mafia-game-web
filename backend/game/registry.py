from __future__ import annotations

import logging
from typing import Dict

from backend.game.composition import build_initial_players
from backend.game.engine import GameEngine
from backend.game.phase import get_phase_duration
from backend.models.game import GameState, Phase
from backend.pod import POD_ID

logger = logging.getLogger("mafia.registry")


class GameRegistry:
    """
    game_id -> GameEngine 매핑 (In-Memory, 단일 서버 개발용).
    게임은 POST /game/create 로만 등록한다 (get_or_create 자동 생성 없음).
    """

    def __init__(self) -> None:
        self._games: Dict[str, GameEngine] = {}

    def get(self, game_id: str) -> GameEngine | None:
        engine = self._games.get(game_id)
        if engine is None:
            logger.warning(
                "[POD=%s] game_id=%s 조회 실패 — 이 POD에 없음"
                " (다른 POD가 소유 중이거나 게임 미생성)",
                POD_ID,
                game_id,
            )
        return engine

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
        logger.info(
            "[POD=%s] 게임 생성 완료 — game_id=%s players=%d"
            " (이 POD가 해당 게임의 단독 소유자)",
            POD_ID,
            game_id,
            len(engine.state.players),
        )
        return engine
