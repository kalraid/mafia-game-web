from __future__ import annotations

import asyncio
import json

import pytest

from backend.agents.analysis_agent import GameInsightAgent


class FakeRedis:
    def __init__(self) -> None:
        self._processed: set[str] = set()
        self._kv: dict[str, bytes] = {}

    def sismember(self, key: str, member: str) -> bool:
        return str(member) in self._processed

    def sadd(self, key: str, *members: str) -> int:
        for m in members:
            self._processed.add(str(m))
        return len(members)

    def get(self, key: str) -> bytes | None:
        return self._kv.get(key)

    def set(self, key: str, val: bytes) -> None:
        self._kv[key] = val


class FakeRAG:
    def __init__(self) -> None:
        self.added: list[tuple[list[str], list[dict] | None]] = []

    def similarity_search(self, query: str, k: int = 3) -> list[dict]:
        return []

    def add_documents(self, texts: object, metadatas: object) -> None:
        self.added.append((list(texts), list(metadatas) if metadatas is not None else None))  # type: ignore[arg-type]


def test_insight_skips_llm_when_already_processed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
    monkeypatch.delenv("CI", raising=False)

    r = FakeRedis()
    r._processed.add("g-done")

    class BadLLM:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def bind_tools(self, tools: object) -> object:  # noqa: ANN401
            raise AssertionError("processed 게임은 analyze 노드까지 가지 않아야 함")

    import langchain_anthropic as la

    monkeypatch.setattr(la, "ChatAnthropic", BadLLM)

    agent = GameInsightAgent(redis_client=r, rag_store=FakeRAG())
    out = asyncio.run(agent.analyze_game("g-done"))
    assert out is False


def test_insight_marks_processed_after_tool_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
    monkeypatch.delenv("CI", raising=False)

    r = FakeRedis()
    r.set("mafia:game_archive:g-new", json.dumps({"game_id": "g-new", "winner": "mafia"}).encode())

    class FakeMsg:
        tool_calls = [
            {"name": "read_game_record", "args": {"game_id": "g-new"}},
            {
                "name": "write_insight_doc",
                "args": {"title": "t1", "category": "strategy", "content": "insight body", "tags": "a,b"},
            },
        ]

    class FakeLLM:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def bind_tools(self, tools: object) -> object:  # noqa: ANN401
            return self

        def invoke(self, messages: object) -> FakeMsg:  # noqa: ANN401
            return FakeMsg()

    import langchain_anthropic as la

    monkeypatch.setattr(la, "ChatAnthropic", FakeLLM)

    rag = FakeRAG()
    agent = GameInsightAgent(redis_client=r, rag_store=rag)
    out = asyncio.run(agent.analyze_game("g-new"))
    assert out is True
    assert r.sismember(GameInsightAgent.PROCESSED_SET_KEY, "g-new")
    assert rag.added
    meta = rag.added[0][1] or []
    assert meta[0].get("source") == "runtime"
    assert meta[0].get("source_game_id") == "g-new"
