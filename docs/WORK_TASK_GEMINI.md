# 📝 Gemini 작업 보고 및 요청 사항 (WORK_TASK_GEMINI)

## 백엔드(Cursor) 및 기획자(Claude) 요청 사항

_(현재 미처리 항목 없음 — 아래 처리됨 이력 참조)_

---

## 처리됨 (이력)

| # | 날짜 | 요약 | 처리 결과 |
|---|------|------|---------|
| GT-1 | 2026-04-06 | G-12 RAG 디버그 패널 rag_context 백엔드 연동 요청 | → Cursor C-16 작업 지시 완료 |
| GT-2 | 2026-04-06 | Phase 5-8 슈퍼바이저 MCP 미구현 보고 | → Cursor C-17 작업 지시 완료 |
| GT-3 | 2026-04-06 | Phase 6-7 AI vs AI 시뮬 미작성 + test_mcp_memory_tools 실패 보고 | → Cursor C-18 작업 지시 완료 |

## 🔴 추가 발견 사항 (2026-04-06)

### [추가 요청] G-9 trust_score 및 player ID 연동
**대상:** Cursor (백엔드)
**내용:** 
1. `backend/game/snapshot.py`: `build_game_state_payload`에서 `trust_score`를 인자로 받아 페이로드에 포함하도록 수정 요망. (현재 프론트엔드는 0.5 고정값 사용 중)
2. `player_death` 이벤트 및 `vote_result` 등의 페이로드에서 `player`를 지칭할 때 `name`과 `id`를 혼용하지 않도록 통일(가급적 `id` 권장)하거나, `players` 리스트에 `id` 필드를 포함시켜 줄 것을 요청함.
