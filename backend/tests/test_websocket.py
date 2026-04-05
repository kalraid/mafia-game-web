from __future__ import annotations

import asyncio
import json

from backend.game.engine import GameEngine
from backend.game.registry import GameRegistry
from backend.models.game import GameState, Phase
from backend.models.game import Player, Role, Team
from backend.websocket.events import ClientToServerEvent, ServerToClientEvent
from backend.websocket.manager import ConnectionManager


def test_websocket_event_models_validate() -> None:
    event = ClientToServerEvent(
        event="chat_message",
        payload={"content": "hi", "sender": "player1"},
    )
    assert event.event == "chat_message"

    msg = ServerToClientEvent(event="game_over", payload={"winner": "citizen", "reason": "test"})
    assert msg.event == "game_over"


def test_connection_manager_can_construct() -> None:
    registry = GameRegistry()
    mgr = ConnectionManager(registry=registry)
    assert mgr is not None


class DummyWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def accept(self) -> None:
        return

    async def send_text(self, text: str) -> None:
        self.sent.append(text)


async def _setup_manager_with_ws(game_id: str, mgr: ConnectionManager, ws: DummyWebSocket) -> None:
    await mgr.connect(game_id=game_id, websocket=ws)  # type: ignore[arg-type]


def _decode_last_event(ws: DummyWebSocket) -> dict:
    assert ws.sent, "no messages captured"
    return json.loads(ws.sent[-1])


def test_websocket_vote_and_use_ability_update_game_state() -> None:
    asyncio.run(_test_websocket_vote_and_use_ability_update_game_state())


async def _test_websocket_vote_and_use_ability_update_game_state() -> None:
    game_id = "ws1"
    registry = GameRegistry()
    registry.create_game(game_id=game_id, host_name="player1", player_count=8)
    game = registry.get(game_id)
    assert game is not None
    target_id = next(p.id for p in game.state.players if p.id != "player1")
    ai_id = next(p.id for p in game.state.players if not p.is_human)

    mgr = ConnectionManager(registry=registry)
    ws = DummyWebSocket()

    await _setup_manager_with_ws(game_id, mgr, ws)

    # chat_message -> stores chat_history and broadcasts
    await mgr.handle_client_message(
        game_id=game_id,
        websocket=ws,  # type: ignore[arg-type]
        raw_text=json.dumps(
            {"event": "chat_message", "payload": {"content": "hi", "sender": "player1"}}
        ),
    )
    assert game.state.chat_history[-1].content == "hi"

    # vote -> updates engine votes and broadcasts vote_result
    await mgr.handle_client_message(
        game_id=game_id,
        websocket=ws,  # type: ignore[arg-type]
        raw_text=json.dumps(
            {"event": "vote", "payload": {"target": target_id, "sender": "player1"}}
        ),
    )
    assert game.get_vote_snapshot()["player1"] == target_id
    last = _decode_last_event(ws)
    assert last["event"] == "vote_result"

    # use_ability -> updates engine ability_requests and broadcasts ability_result
    await mgr.handle_client_message(
        game_id=game_id,
        websocket=ws,  # type: ignore[arg-type]
        raw_text=json.dumps(
            {
                "event": "use_ability",
                "payload": {
                    "target": target_id,
                    "ability": "investigate",
                    "sender": ai_id,
                },
            }
        ),
    )
    assert game.get_ability_snapshot()[ai_id]["ability"] == "investigate"
    last = _decode_last_event(ws)
    assert last["event"] == "ability_result"


def test_websocket_mafia_secret_channel_filtering() -> None:
    asyncio.run(_test_websocket_mafia_secret_channel_filtering())


async def _test_websocket_mafia_secret_channel_filtering() -> None:
    game_id = "ws_filter"
    registry = GameRegistry()
    mgr = ConnectionManager(registry=registry)
    registry.create_game(game_id=game_id, host_name="host", player_count=8)
    game = registry.get(game_id)
    assert game is not None
    game.state.players = [
        Player(id="m1", name="Mafia", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        Player(id="s1", name="Spy", role=Role.SPY, team=Team.NEUTRAL, is_alive=True),
        Player(id="c1", name="Citizen", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
    ]

    ws_mafia = DummyWebSocket()
    ws_spy = DummyWebSocket()
    ws_citizen = DummyWebSocket()
    await mgr.connect(game_id=game_id, websocket=ws_mafia, player_id="m1")  # type: ignore[arg-type]
    await mgr.connect(game_id=game_id, websocket=ws_spy, player_id="s1")  # type: ignore[arg-type]
    await mgr.connect(game_id=game_id, websocket=ws_citizen, player_id="c1")  # type: ignore[arg-type]

    # mafia_secret: 마피아에게만 전송
    await mgr.broadcast(
        game_id,
        ServerToClientEvent(
            event="chat_broadcast",
            payload={
                "sender": "m1",
                "content": "secret",
                "channel": "mafia_secret",
                "timestamp": "t",
                "is_ai": True,
            },
        ),
    )
    assert len(ws_mafia.sent) == 1
    assert len(ws_spy.sent) == 0
    assert len(ws_citizen.sent) == 0

    # spy_listen: 스파이 + 마피아에게 전송
    await mgr.broadcast(
        game_id,
        ServerToClientEvent(
            event="chat_broadcast",
            payload={
                "sender": "m1",
                "content": "listen",
                "channel": "spy_listen",
                "timestamp": "t",
                "is_ai": True,
            },
        ),
    )
    assert len(ws_mafia.sent) == 2
    assert len(ws_spy.sent) == 1
    assert len(ws_citizen.sent) == 0

