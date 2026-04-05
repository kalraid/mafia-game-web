# Cursor → Claude 보고 (Gemini 작업 요청 큐)

> **용도**: Cursor(백엔드)가 프론트·기획 문서 담당 영역에서 필요한 작업을 정리해 두면, Claude가 검토 후 **Gemini**에게 `WORK_ORDER_GEMINI.md` 기준으로 지시한다.  
> **작성**: Cursor | **라우팅**: Claude → Gemini

---

## 미처리 — Gemini 요청 필요

### [WT-1] 로비·세션 — 백엔드 `POST /game/create` 연동 (WORK_ORDER G-13-4 대응)

**배경 (Cursor 구현 완료)**  
- 게임은 반드시 서버에 먼저 등록되어야 함.  
- `POST /game/create` — Body: `{ "host_name": string, "player_count": 4~20 }` — Response: `{ "game_id", "player_count" }`.  
- `GET/POST /game/{game_id}/...` 및 `ws://.../ws/{game_id}` 는 **해당 `game_id`가 Registry에 없으면** REST는 404, WebSocket은 code `4000`으로 종료.  
- 상세: `backend/README.md` API 섹션.

**Gemini 작업 요청 (frontend/)**  
1. `frontend/pages/lobby.py` — 「게임 시작」 시 `BACKEND_URL`로 `POST /game/create` 호출. 성공 시 응답의 `game_id`·`player_count`를 `st.session_state`에 저장 후 게임 페이지로 이동. 실패 시 사용자에게 오류 표시.  
2. `frontend/app.py` — 초기 `game_id` 하드코딩(`test_game` 등) 제거. 로비에서 받은 `game_id`만 사용. WebSocket URL이 생성 전에 열리지 않도록 흐름 정리(필요 시 연결 시점 조정).  
3. (선택) `WORK_ORDER_GEMINI.md` G-12와 충돌 없는지 확인.

**참조**: `docs/planning/WORK_ORDER_GEMINI.md` — G-13-4

---

### [WT-2] `/health`의 `rag_status` 연동 (WORK_ORDER G-12 보조)

**배경 (Cursor 구현 완료)**  
- `GET /health` 응답에 `rag_status` 필드 추가됨. 값: `ok` | `error` | `unknown`  
  - Chroma persist 경로(`CHROMA_PERSIST_DIR`, 기본 `backend/rag/chroma_db`) 존재 및 컬렉션 `ai_mafia_knowledge` 열람 성공 → `ok`  
  - chromadb 미설치/경로 없음 → `unknown`  
  - 열기 실패 등 → `error`  
- 임베딩 모델은 로드하지 않음(경량).

**Gemini 작업 요청 (frontend/)**  
1. 앱 초기화(또는 로비 진입) 시 `GET {BACKEND_URL}/health`로 `rag_status`를 읽어 `st.session_state.rag_status`에 반영 (`ok`/`error`/`unknown` 그대로 사용 가능).  
2. `WORK_ORDER_GEMINI.md` G-12의 RAG 상태 위젯·디버그 패널과 문구를 위 값과 맞출 것.  
3. 백엔드가 내려주지 않는 필드에 의존하는 기존 코드가 있으면 제거 또는 위 스키마로 통일.

**참조**: `docs/planning/WORK_ORDER_GEMINI.md` — G-12, `backend/README.md` — GET /health

---

## 처리됨 (이력)

_(Claude/Gemini 처리 후 여기에 날짜·요약을 남기면 됨.)_
