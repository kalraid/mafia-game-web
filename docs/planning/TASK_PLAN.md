# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.9  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-19  
> **기준 커밋**: `b6d9fe1` (백엔드 작업본 260319-001)

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
Phase 7: UI 다듬기 + 배포             ✅ 대부분 완료 (3서비스 Docker 포함)
```

---

## 2. 작업 항목 상세

### Phase 0: 환경 구성 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 0-1 | 프로젝트 구조 생성 | ✅ | |
| 0-2 | 의존성 정의 | ✅ | 루트 + `frontend/requirements.txt` 분리, playwright 추가 |
| 0-3 | Git 저장소 초기화 | ✅ | |
| 0-4 | 환경변수 설계 | ✅ | `.env.example` |
| 0-5 | Docker 구성 | ✅ | backend(`backend/Dockerfile`) + frontend + redis 3서비스 |
| 0-6 | `.gitignore` 추가 | ✅ | |

---

### Phase 1: 게임 엔진 코어 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 1-1~1-11 | 데이터 모델, Phase, 타이머, 투표, 능력, 승리, GameRunner, Snapshot | ✅ | |
| 1-12 | 게임 로그 | 🔄 부분 | player_death 이벤트만 |

---

### Phase 2: AI Agent 기초 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 2-1 | LangChain + Claude API 연동 | ✅ | `ChatAnthropic` + `with_structured_output` |
| 2-2 | Structured Output 스키마 | ✅ | `AgentDecision` Pydantic |
| 2-3 | Phase별 행동 분기 + 가드 | ✅ | DAY_CHAT / DAY_VOTE / NIGHT_MAFIA / NIGHT_ABILITY |
| 2-4 | Fallback 처리 | ✅ | CI/MAFIA_USE_LLM=0 지원 |
| 2-5 | RAG → Agent 프롬프트 주입 | ✅ | `StrategyRetriever` lazy singleton |
| 2-6 | bind_tools 패턴 | 🔄 부분 | `bind_tools` + `_decision_from_tool_calls()` 구현. 완전한 ToolNode ReAct 루프 미완 |
| 2-7 | 발언 타이밍 딜레이 | ✅ | `_speech_delay()` verbosity 기반 |
| 2-8 | Agent 페르소나/Pool | 🔄 확인 필요 | `persona.py`, `pool.py` 내용 미확인 |
| 2-9 | Redis Checkpointer | 🔄 부분 | `MAFIA_USE_REDIS_CHECKPOINTER=1` 조건부 활성화, 폴백 있음 |

---

### Phase 3: WebSocket + 채팅 UI ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 3-1~3-6 | FastAPI WebSocket + REST API | ✅ | |
| 3-7 | Streamlit 메인 레이아웃 | ✅ | WS_URL 환경변수 지원 |
| 3-8 | 채팅 영역 | ✅ | 마피아 채널 탭 분리, phase 입력 제한 |
| 3-9 | 상태창 | ✅ | |
| 3-10 | 플레이어 카드 | ✅ | CSS 기반 dead-overlay |
| 3-11 | 로비 화면 | ✅ | |
| 3-12 | 게임 화면 | 🔄 확인 필요 | `pages/game.py` 내용 미확인 |
| 3-13 | 결과 화면 | ✅ | winner/직업공개/사망정보/버튼 |
| 3-14 | WebSocket 이벤트 핸들러 | ✅ | player_death, vote_result, ability_result |
| 3-15 | mafia_secret 채널 WS 필터링 | ✅ | `_is_allowed_for_channel()` + `_ws_player_ids` 매핑 |

---

### Phase 4: 슈퍼바이저 + A2A 연동 ✅ 대부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 4-1 | LangGraph StateGraph 도입 | ✅ | |
| 4-2 | 슈퍼바이저 → Agent 지시 흐름 | ✅ | |
| 4-3 | 시민 슈퍼바이저 전략 | ✅ | trust_score + reports 기반 |
| 4-4 | 마피아 슈퍼바이저 전략 | ✅ | detective > doctor > trust_score 우선순위 |
| 4-5 | 중립 슈퍼바이저 | 🔄 확인 필요 | |
| 4-6 | NIGHT_MAFIA 라운드 | ✅ | `run_night_mafia_round()` + mafia_secret |
| 4-7 | A2A Directive 시스템 | ✅ | |
| 4-8 | `_AgentCallState` 직렬화 개선 | ✅ | PlayerAgent 객체 제거, agent_id만 전달, `_invoke_agent()` 헬퍼 |
| 4-9 | 슈퍼바이저 재진단 루프 | ⬜ 미구현 | Phase 종료 후 재진단 없음 |
| 4-10 | Redis Checkpointer 연동 | 🔄 부분 | 조건부 활성화, 폴백 있음 |

---

### Phase 5: RAG + MCP 통합 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 5-1 | ChromaDB RAGStore 구현 | ✅ | |
| 5-2 | 디스크 기반 문서 인덱싱 | ✅ | |
| 5-3 | StrategyRetriever 구현 | ✅ | |
| 5-4 | RAG → Agent 프롬프트 주입 | ✅ | |
| 5-5 | RAG 지식베이스 문서 | 🔄 최소 | 6개 파일 (평가 기준 미달) |
| 5-6 | MCP Tool 구현 | ✅ | `MCPGameTools` |
| 5-7 | MCP bind_tools | 🔄 부분 | bind_tools 적용됨. ToolNode ReAct 루프 미완 |
| 5-8 | 슈퍼바이저 MCP 연동 | ⬜ 미구현 | |

---

### Phase 6: 풀 게임 통합 테스트 🔄 파일 작성

> **테스트 구조**: `backend/tests/` + `frontend/tests/` 각각 보유. 루트 `tests/` 없음.

| # | 작업 | 상태 | 위치 |
|---|------|------|------|
| 6-1 | 게임 엔진 단위 테스트 | 🔄 작성 | `backend/tests/test_game_engine.py` |
| 6-2 | Agent 테스트 | 🔄 업데이트 | `backend/tests/test_agents.py` (bind_tools 카버 추가) |
| 6-3 | WebSocket 테스트 | 🔄 업데이트 | `backend/tests/test_websocket.py` (채널 필터링 카버) |
| 6-4 | 백엔드 pytest 설정 | ✅ | `backend/tests/conftest.py` |
| 6-5 | 프론트 E2E 테스트 | 🔄 작성 | `frontend/tests/e2e/` (playwright 포함) |
| 6-6 | 프론트 유틸 단위 테스트 | 🔄 작성 | `frontend/tests/pytest/` |
| 6-7 | 전체 게임 시뮬레이션 | ⬜ 미작성 | AI vs AI 자동 실행 |

---

### Phase 7: UI 다듬기 + 배포 ✅ 대부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 7-1 | Docker 구성 (backend) | ✅ | `backend/Dockerfile` (b6d9fe1에서 루트 → backend/로 이동) |
| 7-2 | Docker 구성 (frontend) | ✅ | `frontend/Dockerfile` |
| 7-3 | Docker 구성 (redis) | ✅ | docker-compose 관리 (Claude) |
| 7-4 | CSS 스타일링 | ✅ | 낮/밤 테마, dead-overlay |
| 7-5 | 타이머 JS | ✅ | |
| 7-6 | 엔러 처리 유틸 | 🔄 부분 | `handle_request_error()` |
| 7-7 | 결과 화면 | ✅ | |
| 7-8 | README.md | ✅ | |

---

## 3. 현재 이슈 목록 🚨

### 🔴 미해결

| # | 이슈 | 담당 | 조치 |
|---|------|------|------|
| I-1 | MCP bind_tools 완전한 ToolNode ReAct 루프 미완 | Cursor | C-2 추가 작업 |
| I-2 | Redis Checkpointer 조건부 활성화 (MAFIA_USE_REDIS_CHECKPOINTER=1) | Cursor | C-5 폴백 제거 여부 확인 |
| I-3 | RAG 지식베이스 문서 6개 (평가 기준 미달) | Claude | 문서 추가 작성 |
| I-4 | `pages/game.py` 3/4+1/4 레이아웃 미확인 | Gemini | G-7 작업 |

### 🟡 마이너

| # | 이슈 | 담당 |
|---|------|------|
| I-5 | G-1 voter 필드 명시적 확인 커밋 없음 | Gemini |
| I-6 | `is-suspected-N` CSS 클래스 style.css 없음 | Gemini |
| I-7 | 슈퍼바이저 재진단 루프 미구현 | Cursor |

---

## 4. 프로젝트 디렉토리 현황 (2026-03-19 기준)

```
mafia-game-web/
├── .env.example / .gitignore / .nvmrc   ✅
├── docker-compose.yml                   ✅ (Claude 관리 — 3서비스)
├── requirements.txt                     ✅ (langgraph-checkpoint-redis, playwright 추가)
├── README.md / ROLE_*.md                ✅
│
├── docs/planning/                       ✅ 문서 완비
│
├── backend/
│   ├── Dockerfile                       ✅ (루트에서 이동, b6d9fe1)
│   ├── main.py                          ✅
│   ├── websocket/ (manager — 채널 필터링) ✅
│   ├── game/ (engine, runner 등)      ✅
│   ├── agents/ (graph, player_agent)    ✅
│   ├── supervisors/ (citizen, mafia)    ✅
│   ├── rag/ (store, retriever, knowledge/) 🔄 최소
│   ├── mcp/ (tools)                     ✅
│   ├── models/                          ✅
│   └── tests/                           🔄 파일 작성 (업데이트 중)
│
└── frontend/
    ├── Dockerfile                       ✅
    ├── requirements.txt                 ✅
    ├── app.py (WS_URL 환경변수 지원)  ✅
    ├── pages/ (lobby✅, game🔄, result✅) 
    ├── components/ (모두 ✅)            ✅
    ├── assets/style.css                 ✅
    └── tests/                           🔄 파일 작성
```

---

## 5. 최신 커밋 변경 요약

```
커밋 b6d9fe1 — 백엔드 작업본 260319-001
  ✅ websocket/manager.py (C-4 완료):
     - _ws_player_ids: Dict[game_id][WebSocket] → player_id 매핑
     - _is_allowed_for_channel(): mafia_secret=마피아만, spy_listen=마피아+스파이
     - broadcast()에 채널 필터링 적용
     - WebSocket chat_message 이벤트도 GameState.chat_history에 저장
  ✅ agents/graph.py (C-5 부분, 리팩토링):
     - _AgentCallState에서 PlayerAgent 객체 제거 → 직렬화 문제 해결
     - _compile_agent_graph(): MAFIA_USE_REDIS_CHECKPOINTER=1시 RedisSaver, 폴백 있음
     - _invoke_agent() 헬퍼로 구득 통합
  ✅ agents/player_agent.py (C-2 부분):
     - bind_tools([send_chat, submit_vote, use_ability]) 우선 시도
     - _decision_from_tool_calls(): tool_calls 있으면 AgentDecision으로 변환
     - tool_calls 없으면 with_structured_output 폴백
  ✅ requirements.txt: langgraph-checkpoint-redis, playwright 추가
  ✅ backend/Dockerfile: 루트에서 backend/ 폴더로 이동
     → docker-compose.yml dockerfile 경로 업데이트 필요 (Claude 처리)
  🔄 test_agents.py, test_websocket.py 업데이트
```

---

## 6. 다음 우선 작업

### Claude 담당
```
1. RAG 지식 문서 추가 작성 (I-3)
   → backend/rag/knowledge/ 에 20개+ 다양한 문서 필요
```

### Cursor 담당
```
WORK_ORDER_CURSOR.md 참조
낑는 승리: C-4✅, 진행 중: C-2(부분)·C-5(부분)
다음: C-2 ToolNode ReAct 루프 완성 → C-7 roles.py 능력 로직
```

### Gemini 담당
```
WORK_ORDER_GEMINI.md 참조
다음: G-1 확인 → G-7 game.py 레이아웃 → G-9 CSS 정리
```

---

## 7. Git 커밋 규칙

```
feat: 새 기능 / fix: 버그 / docs: 문서
chore: 설정 / test: 테스트 / refactor: 리팩토링
```

## 8. 브랜치 전략

```
master ← 현재 | dev ← Phase5 이후 | feat/* ← 기능별
```
