from __future__ import annotations

from backend.game.engine import GameEngine
from backend.mcp.tools import MCPGameTools
from backend.models.game import GameState, Phase


def create_default_engine() -> GameEngine:
    """
    MCP 서버 구동 시 사용할 기본 GameEngine 인스턴스를 생성하는 헬퍼.
    실제 게임 서버에서는 이미 존재하는 GameEngine을 주입해서 사용.
    """
    dummy_state = GameState(
        game_id="dummy",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=0,
        players=[],
    )
    return GameEngine(dummy_state)


def create_mcp_tools(engine: GameEngine | None = None) -> MCPGameTools:
    if engine is None:
        engine = create_default_engine()
    return MCPGameTools(engine)
