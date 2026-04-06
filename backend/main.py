from __future__ import annotations

import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

# ── 전역 로깅 설정 (FastAPI 앱 생성 전) ───────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("mafia.main")

# ── LangSmith 트레이싱 (LANGCHAIN_TRACING_V2=true 시 verbose/debug) ──
if os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true":
    try:
        from langchain.globals import set_debug, set_verbose

        set_debug(True)
        set_verbose(True)
        logger.info(
            "LangSmith tracing enabled (project=%s)",
            os.getenv("LANGCHAIN_PROJECT", "mafia-game"),
        )
    except ImportError as e:
        logger.warning("LangChain globals 임포트 실패, 트레이싱 플래그만 환경변수로 동작: %s", e)

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from backend.config import get_llm_provider_health
from backend.game.registry import GameRegistry
from backend.pod import POD_ID
from backend.websocket.manager import ConnectionManager
from backend.game.snapshot import build_game_state_payload
from backend.models.chat import ChatMessage
from backend.websocket.events import ServerToClientEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "=== MAFIA BACKEND POD STARTED === pod_id=%s redis=%s checkpointer=%s llm=%s",
        POD_ID,
        os.getenv("REDIS_URL", "N/A"),
        os.getenv("MAFIA_USE_REDIS_CHECKPOINTER", "0"),
        os.getenv("MAFIA_LLM_PROVIDER", "anthropic"),
    )
    yield
    logger.info("=== MAFIA BACKEND POD STOPPING === pod_id=%s", POD_ID)


app = FastAPI(title="AI Mafia Backend", lifespan=lifespan)
registry = GameRegistry()
ws_manager = ConnectionManager(registry=registry)

_game_tasks: dict[str, asyncio.Task] = {}


def _rag_status_for_health() -> str:
    """
    Chroma persist 디렉터리와 컬렉션 메타만 확인한다. SentenceTransformer는 로드하지 않음.
    반환: ok | error | unknown (프론트 G-12와 동일 토큰)
    """
    try:
        import chromadb
    except ImportError:
        return "unknown"

    raw = os.getenv("CHROMA_PERSIST_DIR", "backend/rag/chroma_db")
    path = Path(raw)
    if not path.is_absolute():
        path = (Path(__file__).resolve().parent.parent / path).resolve()
    else:
        path = path.resolve()

    if not path.exists():
        return "unknown"

    try:
        client = chromadb.PersistentClient(path=str(path))
        client.get_or_create_collection("ai_mafia_knowledge")
        return "ok"
    except Exception:
        return "error"


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

    # GameRunner → AgentGraph → RAG 등 무거운 의존성은 루프 시작 시에만 로드한다.
    from backend.game.runner import GameRunner

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
    return {
        "status": "ok",
        "rag_status": _rag_status_for_health(),
        "llm_provider": get_llm_provider_health(),
    }


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
