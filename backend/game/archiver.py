from __future__ import annotations

from typing import Any

from backend.models.game import GameState


class GameArchiver:
    """
    게임 종료 시 GameState를 Redis에 JSON으로 아카이빙한다.
    """

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    def archive(self, state: GameState) -> None:
        key = f"mafia:game_archive:{state.game_id}"
        ttl_seconds = 60 * 60 * 24 * 30  # 30일
        self.redis.setex(key, ttl_seconds, state.model_dump_json())

