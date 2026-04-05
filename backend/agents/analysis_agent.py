from __future__ import annotations

import asyncio
import os
from typing import Any, Protocol, TypedDict

from backend.config import get_chat_llm, is_llm_credentials_available

class _RAGLike(Protocol):
    def similarity_search(self, query: str, k: int = 3) -> list[dict]: ...

    def add_documents(self, texts: Any, metadatas: Any) -> None: ...


class InsightGraphState(TypedDict, total=False):
    """C-10: LangGraph 서브그래프 상태 (gate → analyze → mark)."""

    game_id: str
    skipped: bool
    success: bool


class GameInsightAgent:
    """
    게임 종료 시 기록을 분석해 런타임 RAG 문서를 생성한다.

    - Redis Set `mafia:game_analysis:processed` 로 동일 game_id 중복 분석 방지
    - LangGraph StateGraph: gate(처리 여부) → analyze(LLM+tool) → mark(성공 시 SADD)
    - `mafia:game_archive:{game_id}` 키를 SCAN으로 모아 미분석분만 배치 처리 가능 (`analyze_pending`)
    """

    PROCESSED_SET_KEY = "mafia:game_analysis:processed"
    ARCHIVE_KEY_PREFIX = "mafia:game_archive:"

    def __init__(self, redis_client: Any, rag_store: _RAGLike) -> None:
        self.redis = redis_client
        self.rag_store = rag_store
        self._compiled_graph: Any | None = None

    def _build_graph(self) -> Any:
        from langgraph.graph import END, StateGraph

        redis = self.redis
        processed_key = self.PROCESSED_SET_KEY
        agent = self

        async def node_gate(state: InsightGraphState) -> InsightGraphState:
            gid = str(state.get("game_id") or "")
            is_member = await asyncio.to_thread(redis.sismember, processed_key, gid)
            return {**state, "skipped": bool(is_member), "success": False}

        async def node_analyze(state: InsightGraphState) -> InsightGraphState:
            if state.get("skipped"):
                return {**state, "success": False}
            gid = str(state.get("game_id") or "")
            ok = await agent._run_llm_analysis(gid)
            return {**state, "success": ok}

        async def node_mark(state: InsightGraphState) -> InsightGraphState:
            if state.get("skipped") or not state.get("success"):
                return state
            gid = str(state.get("game_id") or "")
            await asyncio.to_thread(redis.sadd, processed_key, gid)
            return state

        graph: StateGraph = StateGraph(InsightGraphState)
        graph.add_node("gate", node_gate)
        graph.add_node("analyze", node_analyze)
        graph.add_node("mark", node_mark)
        graph.set_entry_point("gate")
        graph.add_edge("gate", "analyze")
        graph.add_edge("analyze", "mark")
        graph.add_edge("mark", END)
        return graph.compile()

    async def analyze_game(self, game_id: str) -> bool:
        use_llm_flag = os.getenv("MAFIA_USE_LLM", "1").strip().lower()
        llm_disabled = os.getenv("CI") is not None or use_llm_flag in {"0", "false", "no"}
        if llm_disabled or not is_llm_credentials_available():
            return False

        if self._compiled_graph is None:
            self._compiled_graph = self._build_graph()

        out: InsightGraphState = await self._compiled_graph.ainvoke({"game_id": game_id})
        return bool(out.get("success"))

    def iter_pending_game_ids(self) -> list[str]:
        """
        Redis에 저장된 아카이브 키(`mafia:game_archive:*`)를 SCAN으로 나열하고,
        `mafia:game_analysis:processed` 에 없는 game_id만 반환한다.
        """
        prefix = self.ARCHIVE_KEY_PREFIX
        match = f"{prefix}*"
        archive_ids: set[str] = set()

        def _decode_key(raw: object) -> str:
            if isinstance(raw, (bytes, bytearray)):
                return raw.decode("utf-8", errors="replace")
            return str(raw)

        scan_iter = getattr(self.redis, "scan_iter", None)
        if not callable(scan_iter):
            return []

        for raw_key in scan_iter(match=match):
            k = _decode_key(raw_key)
            if not k.startswith(prefix):
                continue
            gid = k[len(prefix) :]
            if gid:
                archive_ids.add(gid)

        processed_raw = self.redis.smembers(self.PROCESSED_SET_KEY)
        processed: set[str] = set()
        if processed_raw:
            for p in processed_raw:
                if isinstance(p, (bytes, bytearray)):
                    processed.add(p.decode("utf-8", errors="replace"))
                else:
                    processed.add(str(p))

        pending = archive_ids - processed
        return sorted(pending)

    async def analyze_pending(self, limit: int | None = None) -> list[str]:
        """
        미분석 아카이브에 대해 `analyze_game`을 순차 실행한다.
        성공한 game_id만 목록으로 반환한다.

        - `limit`: 직접 상한. None이면 환경변수 `MAFIA_INSIGHT_PENDING_LIMIT`(정수) 적용,
          그것도 없으면 제한 없음.
        """
        use_llm_flag = os.getenv("MAFIA_USE_LLM", "1").strip().lower()
        llm_disabled = os.getenv("CI") is not None or use_llm_flag in {"0", "false", "no"}
        if llm_disabled or not is_llm_credentials_available():
            return []

        pending = self.iter_pending_game_ids()
        eff_limit = limit
        if eff_limit is None:
            raw = os.getenv("MAFIA_INSIGHT_PENDING_LIMIT", "").strip()
            if raw:
                try:
                    eff_limit = int(raw)
                except ValueError:
                    eff_limit = None
        if eff_limit is not None and eff_limit >= 0:
            pending = pending[: eff_limit]

        analyzed_ok: list[str] = []
        for gid in pending:
            if await self.analyze_game(gid):
                analyzed_ok.append(gid)
        return analyzed_ok

    async def _run_llm_analysis(self, game_id: str) -> bool:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_core.tools import tool

        llm = get_chat_llm(temperature=0)
        if llm is None:
            return False

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
                "source_game_id": game_id,
            }
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
                fn = tool_name_map[name]
                # @tool 로 감싼 Runnable은 invoke(dict) 사용 (직접 **args 호출은 실패할 수 있음)
                inv = getattr(fn, "invoke", None)
                if callable(inv):
                    inv(args)
                else:
                    fn(**args)
                executed_any = True
            except Exception:
                continue

        return executed_any
