from __future__ import annotations

import asyncio

import pytest

from backend.agents.analysis_agent import GameInsightAgent


def test_game_insight_agent_returns_false_when_llm_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "0")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CI", raising=False)

    class FakeRedis:
        pass

    class FakeRAG:
        def similarity_search(self, query: str, k: int = 3) -> list[dict]:
            raise AssertionError("fallback에서 similarity_search는 호출되면 안 됩니다.")

        def add_documents(self, texts, metadatas) -> None:
            raise AssertionError("fallback에서 add_documents는 호출되면 안 됩니다.")

    agent = GameInsightAgent(redis_client=FakeRedis(), rag_store=FakeRAG())
    out = asyncio.run(agent.analyze_game("g-1"))
    assert out is False

