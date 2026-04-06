"""
Phase 6-7: AI vs AI 헤드리스 스모크 — LLM 없이 폴백 에이전트만으로 게임이 종료(winner 설정)되는지 검증.

chromadb 등 무거운 의존성이 없으면 import 단계에서 스킵한다.
"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("chromadb")
pytest.importorskip("sentence_transformers")

from backend.agents.player_agent import PlayerAgent
from backend.game.registry import GameRegistry
from backend.game.runner import GameRunner
from backend.websocket.events import ServerToClientEvent


class _DummyWsManager:
    """WebSocket 없이 GameRunner 루프만 돌리기 위한 스텁."""

    async def broadcast(self, game_id: str, message: ServerToClientEvent) -> None:
        return None


def test_headless_ai_game_reaches_winner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "0")
    monkeypatch.setenv("CI", "1")

    async def _immediate_sleep(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _immediate_sleep)

    # RAG(Chroma 인덱싱·검색)는 턴 수가 많은 헤드리스 루프에서 180s 타임아웃을 자주 유발한다.
    # 본 테스트는 "게임 종료(winner)" 스모크이므로 검색은 끈다.
    PlayerAgent._rag_retriever = None
    monkeypatch.setattr(PlayerAgent, "_get_rag_retriever", lambda self: None)

    registry = GameRegistry()
    gid = "ai_vs_ai_smoke"
    registry.create_game(game_id=gid, host_name="HostHuman", player_count=4)
    engine = registry.get(gid)
    assert engine is not None

    runner = GameRunner(game_id=gid, engine=engine, ws_manager=_DummyWsManager())  # type: ignore[arg-type]

    async def _run() -> None:
        await asyncio.wait_for(runner.run(), timeout=180.0)

    asyncio.run(_run())

    assert engine.state.winner is not None
    assert engine.state.winner in ("citizen", "mafia", "jester")
