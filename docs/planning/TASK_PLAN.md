# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v2.0  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-19  
> **기준 커밋**: `cff6e95` (ROLE_*.md 갱신, AI 전용 파일 추가)

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               ✅ 완료
Phase 2: AI Agent 기초                ✅ 완료 (bind_tools 부분 적용 포함)
Phase 3: WebSocket + 채팅 UI          ✅ 완료 (REST 혼용, 채널 필터링 완료)
Phase 4: 슈퍼바이저 + A2A 연동        ✅ 대부분 완료 (재진단 루프 제외)
Phase 5: RAG + MCP 통합               🔄 부분 완료 (RAG 연결 완료, 지식베이스 최소)
Phase 6: 풀 게임 통합 테스트          🔄 테스트 파일 작성 (실행 여부 미확인)
Phase 7: UI 다듬기 + 배포             ✅ 대부분 완료 (팀 일부 버그 수정 필요)
```

---

## 2. Phase별 작업 항목

### Phase 0 ✅ / Phase 1 ✅ / Phase 2 ✅ / Phase 3 ✅
> 상세 내용은 이전 버전 참조. 현재 대부분 완료.

### Phase 4: 슈퍼바이저 + A2A 연동 ✅ 대부분 완료

| # | 작업 | 상태 |
|---|------|------|
| 4-1~4-8 | LangGraph, 지시 흐름, 시민/마피아 수퍼바이저, NIGHT_MAFIA, A2A, 직렬화 | ✅ |
| 4-9 | 슈퍼바이저 재진단 루프 | ⬜ 미구현 |
| 4-10 | Redis Checkpointer | 🔄 부분 (조건부 활성화) |

### Phase 5: RAG + MCP 통합 🔄 부분 완료

| # | 작업 | 상태 |
|---|------|------|
| 5-1~5-4 | ChromaDB, 인덱싱, Retriever, Agent 주입 | ✅ |
| 5-5 | RAG 지식베이스 문서 | 🔄 6개 (평가 기준 미달) |
| 5-6 | MCP Tool | ✅ MCPGameTools |
| 5-7 | bind_tools | 🔄 ToolNode ReAct 루프 미완 |
| 5-8 | 슈퍼바이저 MCP | ⬜ 미구현 |

### Phase 6: 통합 테스트 🔄 파일 작성

| # | 작업 | 상태 | 위치 |
|---|------|------|------|
| 6-1~6-3 | 백엔드 단위테스트 | 🔄 작성 | `backend/tests/` |
| 6-4 | 백엔드 conftest | ✅ | |
| 6-5~6-6 | 프론트 테스트 | 🔄 작성 | `frontend/tests/` |
| 6-7 | AI vs AI 시뮬레이션 | ⬜ 미작성 | |

### Phase 7: 배포 ✅ 대부분 완료

| # | 작업 | 상태 |
|---|------|------|
| 7-1~7-3 | Docker 3서비스 | ✅ |
| 7-4~7-7 | CSS, 타이머, 결과화면, README | ✅ |
| 7-8 | **CSS 경로 버그** | ❌ **버그** |
| 7-9 | **REST 하드코딩 URL** | 🔄 부분 |

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
| Frontend | ❌ **크래시** | `frontend/assets/style.css` 경로 버그 (아래 설명) |

---

## 4. 현재 버그 목록 (docker-compose 관련) 🚨

### 🔴 [BUG-1] CSS 경로 버그 — **Frontend 컨테이너 크래시 원인**

**파일**: `frontend/app.py`  
**문제**: 컨테이너 내 WORKDIR는 `/app`, 파일은 `COPY . .`로
`/app/assets/style.css`에 이용 되지만 코드는 `frontend/assets/style.css` 경로를 찾음.

```python
# 현재 (❌ 컨테이너에서 실패)
with open("frontend/assets/style.css") as f:

# 수정 후 (✅)
with open("assets/style.css") as f:
```

**담당**: Gemini (G-10)

---

### 🟡 [BUG-2] REST API URL 하드코딩 — 서버 배포 시 변경 필요

**파일**: `frontend/components/status_panel.py`  
**문제**: REST 호출이 `http://localhost:8000/...`으로 하드코딩. `BACKEND_URL` 환경변수를 미사용.

```python
# 현재 (❌ 하드코딩)
response = requests.post(f"http://localhost:8000/game/{game_id}/vote", ...)

# 수정 후 (✅ 환경변수 사용)
backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
response = requests.post(f"{backend_url}/game/{game_id}/vote", ...)
```

**담당**: Gemini (G-11)

---

### ℹ️ [INFO] WS_URL 네트워크 설명

`streamlit-websocket-client`는 브라우저 JS에서 WebSocket을 열기 때문에  
Docker 내부 hostname(`backend`)은 접근 불가. 륌래스탑 docker-compose는:

```
# docker-compose 로컸 테스트 (localhost 접근)
WS_URL=ws://localhost:8000   ← 현재 설정 ✅
BACKEND_URL=http://localhost:8000

# 원격 서버 린치 시
WS_URL=ws://<서버IP>:8000
BACKEND_URL=http://<서버IP>:8000
```

---

## 5. 테스트 가능 여부

### ✅ localhost 모드 (로컸 개발시)

| 테스트 | 가능 | 방법 |
|--------|------|------|
| 백엔드 단위테스트 | ✅ | `cd backend && pytest tests/` (MAFIA_USE_LLM=0) |
| 백엔드 API 수동 테스트 | ✅ | `http://localhost:8000/docs` Swagger UI |
| 프론트 로볼 실행 | ✅ | `streamlit run frontend/app.py` |
| 프론트 단위테스트 | ✅ | `pytest frontend/tests/pytest/` |
| AI 게임 실행 | ✅ | 로비에서 닉네임 입력 후 게임 시작 |

### 🟡 docker-compose 모드 (현재 버그 수정 후 가능)

| 테스트 | 조건 | 후 |
|--------|------|------|
| Redis 동작 | ✅ 바로 | |
| Backend 동작 | ✅ 바로 | |
| Frontend 동작 | ❌ BUG-1 수정 후 | G-10 완료 시 |
| 수동 테스트 (브라우저) | ❌ BUG-1,2 수정 후 | G-10, G-11 완료 시 |
| E2E (Playwright) | ❌ 버그 수정 후 + 테스트 코드 작성 | 6-5 완료 시 |

---

## 6. 현재 이슈 목록

### 🔴 시급

| # | 이슈 | 담당 | 조치 |
|---|------|------|------|
| BUG-1 | `frontend/app.py` CSS 경로 버그 | Gemini | G-10 |
| I-1 | MCP ToolNode ReAct 루프 미완 | Cursor | C-2 |
| I-3 | RAG 지식베이스 6개만 | Claude | 문서 추가 |

### 🟡 중간

| # | 이슈 | 담당 | 조치 |
|---|------|------|------|
| BUG-2 | REST URL 하드코딩 | Gemini | G-11 |
| I-2 | Redis Checkpointer 폴백 제거 | Cursor | C-5 |
| I-4 | `pages/game.py` 레이아웃 미확인 | Gemini | G-7 |
| I-5 | voter 필드 확인 커밋 없음 | Gemini | G-1 |
| I-6 | is-suspected CSS 클래스 없음 | Gemini | G-9 |
| I-7 | 슈퍼바이저 재진단 루프 | Cursor | C-8(신규) |

---

## 7. 다음 우선 작업

### Claude
```
1. RAG 지식 문서 추가 (I-3) → 20개+ 필요
```

### Cursor
```
WORK_ORDER_CURSOR.md 참조
C-2 (ToolNode) → C-5 (Redis 안정화) → C-7 (roles.py)
```

### Gemini
```
WORK_ORDER_GEMINI.md 참조
G-10 (CSS 버그 필수) → G-11 (BACKEND_URL) → G-7 (game.py)
```

---

## 8. Git 커밋 규칙 / 브랜치

```
feat|fix|docs|chore|test|refactor
master ← 현재 | dev ← Phase5 이후 | feat/* ← 기능별
```
