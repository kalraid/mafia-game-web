"""
저장소·실행 cwd와 무관하게 동일한 실경로를 쓰기 위한 경로 헬퍼.

uvicorn/pytest를 `프로젝트 루트` 또는 `backend/`에서 실행해도
`./backend/rag/chroma_db` 같은 상대 env가 `backend/backend/...`로 중첩되지 않게 한다.
"""

from __future__ import annotations

import os
from pathlib import Path

# backend/main.py, backend/paths.py 등이 있는 디렉터리
BACKEND_ROOT: Path = Path(__file__).resolve().parent
# 일반적으로 저장소 루트 (backend/의 부모)
PROJECT_ROOT: Path = BACKEND_ROOT.parent


def resolve_chroma_persist_dir() -> str:
    """CHROMA_PERSIST_DIR 해석. 미설정 시 `backend/rag/chroma_db`(백엔드 패키지 기준)."""
    default = (BACKEND_ROOT / "rag" / "chroma_db").resolve()
    raw = os.getenv("CHROMA_PERSIST_DIR", "").strip()
    if not raw:
        return str(default)

    p = Path(raw).expanduser()
    if p.is_absolute():
        return str(p.resolve())

    normalized = str(p).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[3:]

    # 호스트 .env 관용: ./backend/rag/chroma_db → 저장소 루트 기준
    if normalized.startswith("backend/") or normalized == "backend":
        return str((PROJECT_ROOT / Path(normalized)).resolve())

    return str((BACKEND_ROOT / p).resolve())


def resolve_rag_knowledge_dir() -> str:
    """RAG_KNOWLEDGE_DIR 해석. 미설정 시 저장소 루트의 docs/rag_knowledge."""
    default = (PROJECT_ROOT / "docs" / "rag_knowledge").resolve()
    raw = os.getenv("RAG_KNOWLEDGE_DIR", "").strip()
    if not raw:
        return str(default)

    p = Path(raw).expanduser()
    if p.is_absolute():
        return str(p.resolve())

    normalized = str(p).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[3:]

    if normalized.startswith("docs/") or normalized == "docs":
        return str((PROJECT_ROOT / Path(normalized)).resolve())
    if normalized.startswith("backend/") or normalized == "backend":
        return str((PROJECT_ROOT / Path(normalized)).resolve())

    return str((PROJECT_ROOT / Path(normalized)).resolve())
