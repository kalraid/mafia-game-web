from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Protocol

from backend.rag.store import RAGStore


class _RAGLike(Protocol):
    def similarity_search(self, query: str, k: int = 3) -> list[dict]: ...

    def add_documents(self, texts: Any, metadatas: Any) -> None: ...


@dataclass
class _ToolResult:
    content: str


class GameInsightAgent:
    """
    게임 종료 시 기록(phase 흐름/투표/채팅)을 분석해 런타임 문서를 생성한다.

    MVP 성격으로, LLM 호출이 비활성(ANTHROPIC_API_KEY 없음/CI/MAFIA_USE_LLM=0)인 경우
    아무 것도 하지 않고 False를 반환한다.
    """

    def __init__(self, redis_client: Any, rag_store: _RAGLike) -> None:
        self.redis = redis_client
        self.rag_store = rag_store

    async def analyze_game(self, game_id: str) -> bool:
        use_llm_flag = os.getenv("MAFIA_USE_LLM", "1").strip().lower()
        llm_disabled = os.getenv("CI") is not None or use_llm_flag in {"0", "false", "no"}
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if llm_disabled or not api_key:
            return False

        # Lazy import: 테스트/CI에서 임포트만으로 의존성이 깨지는 것을 방지
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_core.tools import tool

        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4")
        llm = ChatAnthropic(model=model_name, temperature=0, api_key=api_key)

        @tool
        def read_game_record(game_id: str) -> str:
            """Redis에서 완료된 게임 기록을 읽는다."""
            key = f"mafia:game_archive:{game_id}"
            data = self.redis.get(key)
            if not data:
                return "게임 기록 없음"
            return data.decode() if isinstance(data, (bytes, bytearray)) else str(data)

        @tool
        def search_existing_rag(query: str) -> str:
            """기존 RAG에서 유사 문서를 검색해 중복 생성을 방지한다."""
            docs = self.rag_store.similarity_search(query, k=3)
            # RAGStore는 {"text":..., "metadata":...} 형태를 반환한다.
            texts = [d.get("text") or d.get("page_content") or "" for d in docs]
            texts = [t for t in texts if t.strip()]
            return "\n\n".join(texts) if texts else "유사 문서 없음"

        @tool
        def write_insight_doc(title: str, category: str, content: str, tags: str) -> str:
            """분석 결과 문서를 RAGStore에 추가한다. (source=runtime)"""
            metadata = {
                "category": category,
                "title": title,
                "tags": tags,
                "source": "runtime",
            }
            # RAGStore.add_documents(texts, metadatas) 인터페이스를 따른다.
            self.rag_store.add_documents(texts=[content], metadatas=[metadata])
            return f"문서 추가 완료: {title}"

        tool_llm = llm.bind_tools([read_game_record, search_existing_rag, write_insight_doc])

        system_prompt = (
            "너는 게임 데이터 분석 에이전트다. 아래 tool을 사용해서 게임 종료 기록을 읽고, "
            "중복 생성을 피한 뒤 insight 문서를 최소 1개 이상 write_insight_doc tool로 저장하라. "
            "tool 외 일반 텍스트는 출력하지 말라."
        )
        human_prompt = {"game_id": game_id}
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=str(human_prompt))]

        tool_msg = await asyncio.to_thread(tool_llm.invoke, messages)
        tool_calls = getattr(tool_msg, "tool_calls", []) or []
        if not tool_calls:
            return False

        # LangGraph ToolNode를 MVP로 대신해, tool_calls를 수동 실행한다.
        # (PlayerAgent와 동일한 수동 실행 방식)
        tool_name_map = {
            "read_game_record": read_game_record,
            "search_existing_rag": search_existing_rag,
            "write_insight_doc": write_insight_doc,
        }
        executed_any = False
        for tc in tool_calls:
            name = str(tc.get("name", ""))
            args = tc.get("args", {}) or {}
            if name not in tool_name_map:
                continue
            if not isinstance(args, dict):
                continue
            try:
                tool_name_map[name](**args)  # tool은 sync로 실행
                executed_any = True
            except Exception:
                # 하나 실패하더라도 나머지는 계속 시도(최소한의 견고성)
                continue

        return executed_any

