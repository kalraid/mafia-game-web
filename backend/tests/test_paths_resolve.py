from __future__ import annotations

import os
from pathlib import Path

import backend.paths as paths


def test_resolve_chroma_default_points_under_backend_rag() -> None:
    os.environ.pop("CHROMA_PERSIST_DIR", None)
    p = Path(paths.resolve_chroma_persist_dir())
    assert p.name == "chroma_db"
    assert p.parent.name == "rag"
    assert p.parent.parent == paths.BACKEND_ROOT


def test_resolve_chroma_dot_backend_from_env() -> None:
    os.environ["CHROMA_PERSIST_DIR"] = "./backend/rag/chroma_db"
    try:
        p = Path(paths.resolve_chroma_persist_dir()).resolve()
        expected = (paths.PROJECT_ROOT / "backend" / "rag" / "chroma_db").resolve()
        assert p == expected
    finally:
        os.environ.pop("CHROMA_PERSIST_DIR", None)


def test_resolve_rag_knowledge_default_under_docs() -> None:
    os.environ.pop("RAG_KNOWLEDGE_DIR", None)
    p = Path(paths.resolve_rag_knowledge_dir())
    assert p.name == "rag_knowledge"
    assert p.parent.name == "docs"
    assert p.parent.parent == paths.PROJECT_ROOT
