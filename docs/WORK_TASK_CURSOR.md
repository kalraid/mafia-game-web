# Cursor → Claude 보고 (Gemini 작업 요청 큐)

> **용도**: Cursor(백엔드)가 프론트·기획 문서 담당 영역에서 필요한 작업을 정리해 두면, Claude가 검토 후 **Gemini**에게 `WORK_ORDER_GEMINI.md` 기준으로 지시한다.  
> **작성**: Cursor | **라우팅**: Claude → Gemini

---

## 미처리 — Gemini 요청 필요

_(현재 없음)_

---

## 처리됨 (이력)

| # | 날짜 | 요약 |
|---|------|------|
| WT-1 | 2026-04-05 | `POST /game/create` Gemini 연동 완료 — `frontend/pages/lobby.py` (`f5321b6`) |
| WT-2 | 2026-04-05 | `/health rag_status` Gemini 연동 완료 — `status_panel.py`·`app.py` (`e8046d2`) |
