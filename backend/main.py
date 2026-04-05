from __future__ import annotations

import asyncio
import os
import secrets

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from backend.game.registry import GameRegistry
from backend.game.runner import GameRunner
from backend.websocket.manager import ConnectionManager
from backend.game.snapshot import build_game_state_payload
from backend.models.chat import ChatMessage
from backend.websocket.events import ServerToClientEvent


app = FastAPI(title="AI Mafia Backend")
registry = GameRegistry()
ws_manager = ConnectionManager(registry=registry)

_game_tasks: dict[str, asyncio.Task] = {}


class ChatRequest(BaseModel):
    sender: str
    content: str
    channel: str = "global"


class VoteRequest(BaseModel):
    voter: str
    voted_for: str | None = None


class AbilityRequest(BaseModel):
    player_name: str
    ability: str
    target: str


class CreateGameRequest(BaseModel):
    host_name: str = Field(min_length=1, max_length=64)
    player_count: int = Field(ge=4, le=20)


class CreateGameResponse(BaseModel):
    game_id: str
    player_count: int


def _ensure_game_runner(game_id: str) -> None:
    if game_id in _game_tasks:
        return

    engine = registry.get(game_id)
    if engine is None:
        return

    runner = GameRunner(game_id=game_id, engine=engine, ws_manager=ws_manager)
    task = asyncio.create_task(runner.run())

    def _cleanup(_: asyncio.Task) -> None:
        _game_tasks.pop(game_id, None)

    task.add_done_callback(_cleanup)
    _game_tasks[game_id] = task


@app.post("/game/create", response_model=CreateGameResponse)
async def create_game(req: CreateGameRequest) -> CreateGameResponse:
    game_id = f"g_{secrets.token_hex(6)}"
    try:
        registry.create_game(
            game_id=game_id,
            host_name=req.host_name.strip(),
            player_count=req.player_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return CreateGameResponse(game_id=game_id, player_count=req.player_count)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str) -> None:
    player_id = websocket.query_params.get("player_id")
    await ws_manager.connect(game_id, websocket, player_id=player_id)
    if registry.get(game_id) is None:
        await websocket.close(code=4000, reason="unknown game")
        ws_manager.disconnect(game_id, websocket)
        return
    _ensure_game_runner(game_id)
    try:
        while True:
            text = await websocket.receive_text()
            await ws_manager.handle_client_message(game_id, websocket, text)
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, websocket)
    except Exception:
        # 런타임 오류 시에도 연결을 정리한다.
        ws_manager.disconnect(game_id, websocket)


@app.post("/game/{game_id}/chat")
async def post_chat(game_id: str, req: ChatRequest) -> dict[str, str]:
    game = registry.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    _ensure_game_runner(game_id)

    msg = ChatMessage(
        id=f"chat_{len(game.state.chat_history)+1}",
        sender=req.sender,
        content=req.content,
        channel=req.channel,
        timestamp=__import__("datetime").datetime.utcnow(),
        is_ai=False,
    )
    game.state.chat_history.append(msg)

    await ws_manager.broadcast(
        game_id,
        ServerToClientEvent(
            event="chat_broadcast",
            payload={
                "sender": req.sender,
                "content": req.content,
                "channel": req.channel,
                "timestamp": msg.timestamp.isoformat(),
                "is_ai": False,
            },
        ),
    )
    return {"status": "ok"}


@app.post("/game/{game_id}/vote")
async def post_vote(game_id: str, req: VoteRequest) -> dict[str, str]:
    game = registry.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    _ensure_game_runner(game_id)

    if req.voted_for is not None:
        game.submit_vote(voter_id=req.voter, target_id=req.voted_for)

    payload = build_game_state_payload(game)
    await ws_manager.broadcast(
        game_id,
        ServerToClientEvent(
            event="game_state_update",
            payload={
                "players": payload["players"],
                "phase": payload["phase"],
                "round": payload["round"],
                "timer_seconds": payload["timer_seconds"],
            },
        ),
    )
    return {"status": "ok"}


@app.post("/game/{game_id}/ability")
async def post_ability(game_id: str, req: AbilityRequest) -> dict[str, str]:
    game = registry.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    _ensure_game_runner(game_id)

    ability = req.ability
    # 프론트의 "protect" → 엔진의 "heal" 매핑
    if ability == "protect":
        ability = "heal"

    game.submit_ability(agent_id=req.player_name, ability=ability, target_id=req.target)

    await ws_manager.broadcast(
        game_id,
        ServerToClientEvent(
            event="ability_result",
            payload={
                "type": ability,
                "success": True,
                "detail": {"target": req.target},
            },
        ),
    )

    payload = build_game_state_payload(game)
    await ws_manager.broadcast(
        game_id,
        ServerToClientEvent(
            event="game_state_update",
            payload={
                "players": payload["players"],
                "phase": payload["phase"],
                "round": payload["round"],
                "timer_seconds": payload["timer_seconds"],
            },
        ),
    )

    return {"status": "ok"}


def get_port() -> int:
    port_str = os.getenv("PORT", "8000")
    try:
        return int(port_str)
    except ValueError:
        return 8000
