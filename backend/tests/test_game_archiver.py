from __future__ import annotations

import json

from backend.game.archiver import GameArchiver
from backend.models.game import GameState, Phase, Player, Role, Team


def test_game_archiver_archive_calls_redis_setex_with_expected_payload() -> None:
    captured: dict[str, object] = {}

    class FakeRedis:
        def setex(self, key: str, time: int, value: str) -> None:
            captured["key"] = key
            captured["time"] = time
            captured["value"] = value

    redis_client = FakeRedis()
    archiver = GameArchiver(redis_client=redis_client)

    state = GameState(
        game_id="g-archiver-1",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=180,
        players=[Player(id="p1", name="A", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True)],
    )

    archiver.archive(state)

    assert captured["key"] == "mafia:game_archive:g-archiver-1"
    assert captured["time"] == 60 * 60 * 24 * 30

    payload = json.loads(str(captured["value"]))
    assert payload["game_id"] == "g-archiver-1"
    assert payload["phase"] == "day_chat"

