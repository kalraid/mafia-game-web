# Cursor → Claude 보고 (Gemini 작업 요청 큐)

> **용도**: Cursor(백엔드)가 프론트·기획 문서 담당 영역에서 필요한 작업을 정리해 두면, Claude가 검토 후 **Gemini**에게 `WORK_ORDER_GEMINI.md` 기준으로 지시한다.  
> **작성**: Cursor | **라우팅**: Claude → Gemini

---

## 미처리 — Gemini 요청 필요

### [WT-3] `/health`의 `llm_provider` 표시 (선택, WORK_ORDER C-12-4 보조)

**배경 (Cursor 구현 완료)**  
- `GET /health` 응답에 `llm_provider` 추가: `anthropic` | `azure` | `disabled` | `fallback`  
- `MAFIA_USE_LLM=0` → `disabled`, 자격 증명 없으면 `fallback`, Azure/Anthropic 각각 설정 시 해당 값.

**Gemini 작업 요청 (frontend/)**  
1. (선택) 로비 또는 사이드바에 현재 백엔드 LLM 모드를 한 줄로 표시 (`st.caption` 등).  
2. `GET /health`에서 `llm_provider` 키를 읽어 `st.session_state`에 캐시해도 됨.

**참조**: `docs/planning/WORK_ORDER_CURSOR.md` — C-12-4, `backend/README.md`

---

## 처리됨 (이력)

| # | 날짜 | 요약 |
|---|------|------|
| WT-1 | 2026-04-05 | `POST /game/create` Gemini 연동 완료 — `frontend/pages/lobby.py` (`f5321b6`) |
| WT-2 | 2026-04-05 | `/health rag_status` Gemini 연동 완료 — `status_panel.py`·`app.py` (`e8046d2`) |
