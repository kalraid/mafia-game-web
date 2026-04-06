# Frontend — AI Mafia Online

> **담당**: Gemini AI  
> **이 파일은 Gemini가 직접 관리합니다.** 내용 변경 시 `.geminirules` 규칙을 준수할 것.

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| Streamlit | >= 1.32 |
| streamlit-websocket-client | 0.0.1 |
| requests | HTTP REST 호출 |
| playwright | E2E 테스트 |

---

## 로컬 실행

```bash
# frontend/ 폴더에서 또는 프로젝트 루트에서

# 1. 의존성 설치
pip install -r frontend/requirements.txt

# 2. 백엔드가 먼저 실행 중이어야 합니다
#    http://localhost:8000/health 확인

# 3. Streamlit 실행
streamlit run frontend/app.py

# 4. 브라우저에서 접속
#    http://localhost:8501
```

---

## 환경변수

```env
WS_URL=ws://localhost:8000       # WebSocket 서버 주소 (브라우저 접근 가능 URL)
BACKEND_URL=http://localhost:8000 # REST API 서버 주소
```

> ⚠️ `WS_URL` 은 브라우저 JS 에서 직접 접근하는 주소입니다.  
> Docker 환경에서도 `ws://localhost:8000` 을 사용합니다 (컨테이너 내부 hostname 불가).

---

## 테스트 실행

```bash
# 단위 테스트
pytest frontend/tests/pytest/ -v

# E2E 테스트 (백엔드 실행 중 필요)
pytest frontend/tests/e2e/ -v

# Playwright 브라우저 설치 (최초 1회)
playwright install chromium
```

---

## 디렉토리 구조

```
frontend/
├── README.md              ← 이 파일 (Gemini 관리)
├── Dockerfile
├── requirements.txt
├── app.py                 ← Streamlit 메인 앱 + WebSocket 핸들러
├── utils.py               ← 공통 유틸 (에러 처리 등)
├── pages/
│   ├── lobby.py           ← 로비 화면 (닉네임/인원 입력)
│   ├── game.py            ← 게임 화면 (3/4 채팅 + 1/4 상태창)
│   └── result.py          ← 결과 화면 (승패/직업 공개)
├── components/
│   ├── chat_area.py       ← 채팅 영역 (채널별 탭 포함)
│   ├── status_panel.py    ← 상태창 (타이머/플레이어/버튼)
│   └── player_card.py     ← 플레이어 카드 (사망 오버레이)
├── assets/
│   └── style.css          ← 낮/밤 테마, 채팅 스타일
└── tests/
    ├── e2e/               ← Playwright E2E 테스트
    └── pytest/            ← 단위 테스트
```

---

## 화면 구성

```
로비 → 게임 화면 → 결과 화면

[게임 화면]
┌─────────────────────────┬──────────────┐
│                         │  ☀️ 낮 2R   │
│       채팅 영역          │  ⏱ 02:14   │
│      (가로 3/4)          ├──────────────┤
│                         │  플레이어    │
│  - 전체 채팅 탭          │  목록 (카드) │
│  - 🔴 마피아 채널 탭     ├──────────────┤
│    (마피아 역할 시만)     │  Phase별     │
│                         │  버튼 영역   │
└─────────────────────────┴──────────────┘
```

---

## WebSocket 이벤트 처리

| 수신 이벤트 | 처리 내용 |
|------------|----------|
| `chat_broadcast` | 채팅 히스토리 추가 |
| `phase_change` | Phase 표시 + 테마 전환 |
| `game_state_update` | 전체 상태 갱신 |
| `player_death` | 사망 오버레이 적용 (`player_id` + 표시용 `player` 이름) |
| `vote_result` | 투표 수 업데이트 (`votes_received`: 플레이어 id 기준 득표 집계) |
| `ability_result` | 토스트 메시지 |
| `game_over` | 결과 화면 전환 |

## REST 송신

| 액션 | 엔드포인트 | Body | 비고 |
|------|-----------|------|------|
| 게임 생성 | `POST /game/create` | `{ host_name, player_count }` | 로비에서 호출 (G-13-4) |
| 채팅 | `POST /game/{id}/chat` | `{ sender, content, channel }` | |
| 투표 | `POST /game/{id}/vote` | `{ voter, voted_for }` | |
| 능력 | `POST /game/{id}/ability` | `{ player_name, ability, target }` | |

---

## 주요 기능 및 구성

### 1. 게임 생성 (G-13-4)
로비(`pages/lobby.py`)에서 닉네임과 인원수를 설정한 후 "게임 시작" 버튼을 누르면 백엔드에 게임 생성을 요청합니다. 성공 시 발급된 `game_id`를 기반으로 게임 화면으로 이동합니다.

### 2. RAG · 슈퍼바이저 / MCP 디버그 패널 (G-12, C-16/C-17)
상태창(`components/status_panel.py`) 하단 **「RAG 컨텍스트 (디버그)」** expander에서 AI가 참조한 `rag_context` 히트를 확인할 수 있습니다. **「슈퍼바이저 / MCP (디버그)」** expander에서는 `game_state_update`에 실리는 `debug_directives`(슈퍼바이저 지시)와 `debug_reports`(`report_to_supervisor` 적재분)를 볼 수 있습니다.

### 3. 서버 상태 모니터링 (G-15, G-16) — G-17
상태창에서 백엔드 연결 여부와 `GET /health`의 `rag_status` 뱃지를 표시합니다. **G-16**: 동일 영역에 LLM Provider 뱃지를 표시하며, 값은 `anthropic` / `azure` / `disabled` / `fallback` 중 하나입니다(헬스 응답의 `llm_provider`와 동기).

### 4. WebSocket 핸들러 (app.py)
`streamlit-websocket-client`를 통해 백엔드와 실시간으로 통신하며, 수신된 이벤트에 따라 세션 상태(`st.session_state.game_state`)를 업데이트하고 화면을 자동으로 갱신(Rerun)합니다.

---

## Dockerfile

```bash
# frontend/ 폴더에서 빌드
docker build -f frontend/Dockerfile -t mafia-frontend ./frontend
```
