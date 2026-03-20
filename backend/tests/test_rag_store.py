from __future__ import annotations

from backend.rag.store import RAGStore


def test_extract_frontmatter_parses_key_value_and_splits_body() -> None:
    md = (
        "# title\n\n"
        "category: strategy\n"
        "role: mafia\n"
        "team: mafia\n"
        "difficulty: basic\n"
        "---\n"
        "## body\n"
        "content here\n"
    )

    meta, body = RAGStore._extract_frontmatter(md)

    assert meta["category"] == "strategy"
    assert meta["role"] == "mafia"
    assert meta["team"] == "mafia"
    assert meta["difficulty"] == "basic"
    assert "## body" in body
    assert "category: strategy" not in body


def test_extract_frontmatter_returns_original_when_no_delimiter() -> None:
    md = "# title\n\nbody only"
    meta, body = RAGStore._extract_frontmatter(md)
    assert meta == {}
    assert body == md

