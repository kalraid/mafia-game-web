from __future__ import annotations

import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.websocket.manager import ConnectionManager


app = FastAPI(title="AI Mafia Backend")
ws_manager = ConnectionManager()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str) -> None:
    await ws_manager.connect(game_id, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            await ws_manager.handle_client_message(game_id, websocket, text)
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, websocket)


def get_port() -> int:
    port_str = os.getenv("PORT", "8000")
    try:
        return int(port_str)
    except ValueError:
        return 8000
