from __future__ import annotations

import asyncio

import pytest

from backend.agents.analysis_agent import GameInsightAgent


class FakeRedisScan:
    """scan_iter / smembers 지원 최소 Fake (단위 테스트용)."""

    def __init__(self) -> None:
        self._kv: dict[str, bytes] = {}
        self._processed: set[str] = set()

    def scan_iter(self, match: str = "*") -> object:
        prefix = "mafia:game_archive:"
        if match.endswith("*") and match.startswith(prefix):
            p = match[:-1]
        else:
            p = prefix
        for k in sorted(self._kv.keys()):
            if k.startswith(p):
                yield k.encode("utf-8")

    def smembers(self, key: str) -> set[bytes]:
        if key == GameInsightAgent.PROCESSED_SET_KEY:
            return {x.encode("utf-8") for x in self._processed}
        return set()

    def get(self, key: str) -> bytes | None:
        return self._kv.get(key)

    def sismember(self, key: str, member: str) -> bool:
        if key == GameInsightAgent.PROCESSED_SET_KEY:
            return str(member) in self._processed
        return False

    def sadd(self, key: str, *members: str) -> int:
        if key == GameInsightAgent.PROCESSED_SET_KEY:
            for m in members:
                self._processed.add(str(m))
            return len(members)
        return 0

    def set_archive(self, game_id: str, payload: bytes) -> None:
        self._kv[f"mafia:game_archive:{game_id}"] = payload


class FakeRAG:
    def similarity_search(self, query: str, k: int = 3) -> list[dict]:
        return []

    def add_documents(self, texts: object, metadatas: object) -> None:
        pass


def test_iter_pending_game_ids_excludes_processed() -> None:
    r = FakeRedisScan()
    r.set_archive("a", b"{}")
    r.set_archive("b", b"{}")
    r.set_archive("c", b"{}")
    r._processed.add("b")

    agent = GameInsightAgent(redis_client=r, rag_store=FakeRAG())
    assert agent.iter_pending_game_ids() == ["a", "c"]


def test_analyze_pending_respects_limit_and_calls_analyze(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("MAFIA_INSIGHT_PENDING_LIMIT", raising=False)

    r = FakeRedisScan()
    for gid in ("z", "y", "x"):
        r.set_archive(gid, b"{}")

    calls: list[str] = []

    agent = GameInsightAgent(redis_client=r, rag_store=FakeRAG())

    async def stub_analyze(game_id: str) -> bool:
        calls.append(game_id)
        return True

    monkeypatch.setattr(agent, "analyze_game", stub_analyze)

    out = asyncio.run(agent.analyze_pending(limit=2))
    assert out == ["x", "y"]
    assert calls == ["x", "y"]
