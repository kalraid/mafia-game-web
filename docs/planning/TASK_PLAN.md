# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v2.3
> **최초 작성일**: 2026-03-18
> **최종 업데이트**: 2026-04-05 (C-12/G-16 완료, .env+docker-compose AOAI 항목 추가)
> **기준 커밋**: `e180eb6`

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               ✅ 완료
Phase 2: AI Agent 기초                ✅ 완료 (bind_tools 부분 적용 포함)
Phase 3: WebSocket + 채팅 UI          ✅ 완료 (REST 혼용, 채널 필터링 완료)
Phase 4: 슈퍼바이저 + A2A 연동        ✅ 완료 (재진단 루프 포함 C-8 완료)
Phase 5: RAG + MCP 통합               ✅ 완료 (C-9 인덱싱, C-2 ToolNode 완료)
Phase 6: 풀 게임 통합 테스트          🔄 부분 완료 (단위 테스트 추가, E2E/AI 시뮬 미완)
Phase 7: UI 다듬기 + 배포             ✅ 완료 (G-13/G-14/G-12 모두 완료)
Phase 8: GameInsightAgent — 게임 결과 RAG 자동 업데이트  ✅ 완료 (C-10 전체)
```

---

## 2. Phase별 작업 항목

### Phase 0 ✅ / Phase 1 ✅ / Phase 2 ✅ / Phase 3 ✅
> 상세 내용은 이전 버전 참조. 현재 대부분 완료.

### Phase 4: 슈퍼바이저 + A2A 연동 ✅ 완료

| # | 작업 | 상태 |
|---|------|------|
| 4-1~4-8 | LangGraph, 지시 흐름, 시민/마피아 수퍼바이저, NIGHT_MAFIA, A2A, 직렬화 | ✅ |
| 4-9 | 슈퍼바이저 재진단 루프 | ✅ C-8 완료 |
| 4-10 | Redis Checkpointer | 🔄 부분 (조건부 활성화, C-5 잔존) |

### Phase 5: RAG + MCP 통합 ✅ 완료

| # | 작업 | 상태 |
|---|------|------|
| 5-1~5-4 | ChromaDB, 인덱싱, Retriever, Agent 주입 | ✅ |
| 5-5 | RAG 지식베이스 문서 | ✅ 20개 → C-9 인덱싱 완료 |
| 5-6 | MCP Tool | ✅ MCPGameTools |
| 5-7 | bind_tools | ✅ C-2 ToolNode ReAct 루프 완료 |
| 5-8 | 슈퍼바이저 MCP | ⬜ 미구현 |

### Phase 6: 통합 테스트 🔄 부분 완료

| # | 작업 | 상태 | 위치 |
|---|------|------|------|
| 6-1~6-3 | 백엔드 단위테스트 | ✅ (API·WebSocket·health 테스트 추가, `7673e40`·`5f7175a`) | `backend/tests/` |
| 6-4 | 백엔드 conftest | ✅ | |
| 6-5 | 프론트 E2E (Playwright) | ✅ 셀렉터 수정 (`9c829fc`) | `frontend/tests/e2e/` |
| 6-6 | 프론트 단위테스트 | ✅ role color utility (`ab8054a`) | `frontend/tests/pytest/` |
| 6-7 | AI vs AI 시뮬레이션 | ⬜ 미작성 | |

### Phase 7: 배포 ✅ 대부분 완료

| # | 작업 | 상태 |
|---|------|------|
| 7-1~7-3 | Docker 3서비스 | ✅ |
| 7-4~7-7 | CSS, 타이머, 결과화면, README | ✅ |
| 7-8 | CSS 경로 버그 (`app.py` os.path.join 방식) | ✅ 수정완료 (G-10) |
| 7-9 | REST URL 환경변수화 (`BACKEND_URL`) | ✅ 수정완료 (G-11) |

---

### Phase 8: GameInsightAgent — 게임 결과 RAG 자동 업데이트 ✅ 완료

**목표**: 게임 종료 시 실전 데이터를 분석해 RAG 지식베이스에 자동 추가 → AI 플레이 품질 점진적 향상

**데이터 파이프라인**:
```
GameEngine (GameState) → [게임 종료 hook] → Redis mafia:game_archive:{game_id}
  → GameInsightAgent (LangGraph ReAct) → RAGStore.add_documents() → ChromaDB
```

| # | 작업 | 상태 | 파일 | 담당 |
|---|------|------|------|------|
| 8-1 | GameArchiver — 게임 종료 시 Redis 아카이브 | ✅ `e531163` | `backend/game/archiver.py` | Cursor |
| 8-2 | GameInsightAgent — LangGraph StateGraph + bind_tools | ✅ `61a4ff4` | `backend/agents/analysis_agent.py` | Cursor |
| 8-3 | runner.py — 게임 종료 hook 추가 | ✅ `7f080d4` | `backend/game/runner.py` | Cursor |
| 8-4 | RAGStore — `source="runtime"` 메타데이터 구분 | ✅ `387ea8a` | `backend/rag/store.py` | Cursor |

**새 Redis 키**:
```
mafia:game_archive:{game_id}       String (JSON)  TTL 30일
mafia:game_analysis:processed      Set            중복 방지
```

**참조**: `RAG_AND_STORAGE_DESIGN.md` §8, `WORK_ORDER_CURSOR.md` C-10

---

## 3. docker-compose 실행 가능 여부 분석

### 실행 명령
```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 편집: ANTHROPIC_API_KEY 입력 (없으면 Fallback 모드)

# 2. 빌드 및 실행
docker-compose up --build

# 3. 접속
# 프론트:   http://localhost:8501
# 백엔드:   http://localhost:8000/docs
# Redis:   localhost:6379
```

### 서비스별 실행 시작 가능 여부

| 서비스 | 실행 | 비고 |
|--------|------|------|
| Redis | ✅ 바로 가능 | `redis:7-alpine` 표준 이미지 |
| Backend | ✅ 바로 가능 | ANTHROPIC_API_KEY 없으면 Fallback 모드로 동작 |
| Frontend | ✅ 바로 가능 | G-10 경로 버그 수정 완료 |

---

## 4. 현재 버그 목록 🚨 (2026-04-05 기준)

### ✅ 모든 긴급 버그 해소

### ✅ 수정 완료

| # | 내용 | 커밋 |
|---|------|------|
| ~~BUG-1~~ | CSS 경로 버그 (`os.path.join` 방식) | G-10 |
| ~~BUG-2~~ | REST URL 하드코딩 → `BACKEND_URL` 환경변수 | G-11 |
| ~~BUG-B1~~ | `snapshot.py` FINAL_VOTE → "final_vote" 수정 | `5f45e53` |
| ~~BUG-B2~~ | `mcp/tools.py` submit_vote 파라미터 통일 | `345831e` |
| ~~BUG-B3~~ | `roles.py` FORTUNE_TELLER/SPY handler 추가 | `1a79641` |
| ~~BUG-F1~~ | `app.py` L78 message 변수 충돌 수정 | `8fb383e` |
| ~~BUG-F2~~ | `app.py` phase 초기값 "lobby" 수정 | `c973057` |
| ~~BUG-F3~~ | `status_panel.py` final_speech 버튼 구현 | `f8d28cf` |
| ~~BUG-F5~7~~ | E2E 테스트 셀렉터 3건 수정 | `9c829fc` |
| ~~BUG-F4~~ | `lobby.py` `POST /game/create` 연동 | `f5321b6` |

### ℹ️ [INFO] WS_URL 네트워크 설명

`streamlit-websocket-client`는 브라우저 JS에서 WebSocket을 열기 때문에
Docker 내부 hostname(`backend`)은 접근 불가.

```
# docker-compose 로컬 테스트
WS_URL=ws://localhost:8000   ← 현재 설정 ✅
BACKEND_URL=http://localhost:8000

# 원격 서버 배포 시
WS_URL=ws://<서버IP>:8000
BACKEND_URL=http://<서버IP>:8000
```

---

## 5. 테스트 가능 여부

### ✅ localhost 모드 (로컬 개발 시)

| 테스트 | 가능 | 방법 |
|--------|------|------|
| 백엔드 단위테스트 | ✅ | `cd backend && pytest tests/` (MAFIA_USE_LLM=0) |
| 백엔드 API 수동 테스트 | ✅ | `http://localhost:8000/docs` Swagger UI |
| 프론트 로컬 실행 | ✅ | `streamlit run frontend/app.py` |
| 프론트 단위테스트 | ✅ | `pytest frontend/tests/pytest/` |
| AI 게임 실행 | ✅ | 로비에서 닉네임 입력 후 게임 시작 |

### 🟡 docker-compose 모드 (현재 버그 수정 후 가능)

| 테스트 | 조건 | 후 |
|--------|------|------|
| Redis 동작 | ✅ 바로 | |
| Backend 동작 | ✅ 바로 | |
| Frontend 동작 | ✅ G-10 완료 | |
| 수동 테스트 (브라우저) | ✅ G-10, G-11 완료 | |
| E2E (Playwright) | ❌ 버그 수정 후 + 테스트 코드 작성 | 6-5 완료 시 |

---

## 6. 현재 이슈 목록 (2026-04-05 기준)

### 🔴 시급 — 즉시 수정

_(시급 이슈 없음)_

### 🟡 신규 작업

_(현재 없음)_

### ✅ 해소된 이슈

| # | 내용 |
|---|------|
| ~~BUG-1~~ | CSS 경로 버그 (G-10) |
| ~~BUG-2~~ | REST URL 하드코딩 (G-11) |
| ~~BUG-B1~3~~ | 백엔드 버그 3건 (C-11, `5f45e53`~`1a79641`) |
| ~~BUG-F1~3~~ | 프론트 버그 3건 (G-13-1~3, `8fb383e`~`f8d28cf`) |
| ~~BUG-F4~~ | `lobby.py` 세션 생성 API 연동 (G-13-4, `f5321b6`) |
| ~~BUG-F5~7~~ | E2E 셀렉터 (G-14, `9c829fc`) |
| ~~I-1~~ | MCP ToolNode ReAct 루프 (C-2, `91150e0`) |
| ~~I-7~~ | 슈퍼바이저 재진단 루프 (C-8, `96becae`) |
| ~~I-3~~ | RAG 지식베이스 인덱싱 (C-9, `c77e002`) |
| ~~I-4~~ | `pages/game.py` 레이아웃 (G-7) |
| ~~I-5~~ | voter 필드 (G-1) |
| ~~I-6~~ | is-suspected CSS (G-9) |
| ~~I-8~~ | GameRegistry 동적 로비 + `POST /game/create` + 인원별 직업 구성 (`1baa68f`) |
| ~~I-2~~ | Redis Checkpointer 폴백 제거 (C-5, `5b557a0`) |
| ~~Phase 8~~ | GameInsightAgent 전체 (C-10, `e531163`~`d691e80`) |
| ~~I-9~~ | LLM Provider config 레이어 — `backend/config.py` (C-12, `f25160f`) |
| ~~I-10~~ | LLM provider 뱃지 표시 (G-16, `e180eb6`) |
| ~~I-9 인프라~~ | `.env.example` / `docker-compose.yml` AOAI_* 추가 (Claude) |

---

## 7. 다음 우선 작업

### Claude
```
✅ .env.example AOAI_* 항목 추가 완료
✅ docker-compose.yml AOAI_* pass-through 추가 완료
```

### Cursor
```
현재 지시된 작업 없음 — 대기 중
```

### Gemini
```
현재 지시된 작업 없음 — 대기 중
```

---

## 8. Git 커밋 규칙 / 브랜치

```
feat|fix|docs|chore|test|refactor
master ← 현재 | dev ← Phase5 이후 | feat/* ← 기능별
```
