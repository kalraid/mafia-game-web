# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.6  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-19  
> **기준 커밋**: `cca37b07` (프론트 수정안 260319)

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               ✅ 완료
Phase 2: AI Agent 기초                ✅ 완료 (LLM 연동, Structured Output, Fallback)
Phase 3: WebSocket + 채팅 UI          ✅ 완료 (REST API 방식 혼용)
Phase 4: 슈퍼바이저 + A2A 연동        🔄 부분 완료 (LangGraph 도입, 전략 로직 미완)
Phase 5: RAG + MCP 통합               🔄 부분 완료 (ChromaDB 구현, 지식베이스 최소 수준)
Phase 6: 풀 게임 통합 테스트          🔄 테스트 파일 작성 (실행 여부 미확인)
Phase 7: UI 다듬기 + 배포             🔄 컴포넌트·로비·마피아 채널 완료, 결과화면 미완
```

---

## 2. 작업 항목 상세

### Phase 0: 환경 구성 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 0-1 | 프로젝트 구조 생성 | ✅ 완료 | |
| 0-2 | 의존성 정의 | ✅ 완료 | `requirements.txt` 지속 업데이트 중 |
| 0-3 | Git 저장소 초기화 | ✅ 완료 | |
| 0-4 | 환경변수 설계 | ✅ 완료 | `.env.example` 업데이트됨 |
| 0-5 | Docker 구성 | ✅ 완료 | `Dockerfile`, `docker-compose.yml` |

---

### Phase 1: 게임 엔진 코어 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 1-1 | 데이터 모델 정의 | ✅ 완료 | `models/game.py` 완성 |
| 1-2 | Phase Manager | ✅ 완료 | `game/phase.py` 구현 |
| 1-3 | 타이머 시스템 | ✅ 완료 | `GameRunner.run()` asyncio 루프로 통합 |
| 1-4 | 직업 배분 로직 | ✅ 완료 | `game/registry.py` + `engine` 연동 |
| 1-5 | 투표 시스템 | ✅ 완료 | `vote.py` tally + `engine.submit_vote()` |
| 1-6 | 직업 능력 처리 | ✅ 완료 | `engine.submit_ability()` 구현 |
| 1-7 | 승리 조건 판정 | ✅ 완료 | `win_condition.py` 구현 |
| 1-8 | 게임 엔진 코어 | ✅ 완료 | `engine.py` Phase 전환 + 능력 결과 처리 |
| 1-9 | GameRegistry | ✅ 완료 | `registry.py` In-Memory 세션 관리 |
| 1-10 | GameRunner | ✅ 완료 | `runner.py` — 게임 루프 + WS 브로드캐스트 조율 |
| 1-11 | GameSnapshot | ✅ 완료 | `snapshot.py` — 게임 상태 payload 빌드 |
| 1-12 | 게임 로그 | 🔄 부분 | `player_death` 이벤트만 로깅, 전체 로그 미완 |

---

### Phase 2: AI Agent 기초 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 2-1 | LangChain + Claude API 연동 | ✅ 완료 | `ChatAnthropic` + `with_structured_output` |
| 2-2 | Structured Output 스키마 | ✅ 완료 | `AgentDecision` Pydantic 모델 |
| 2-3 | Phase별 행동 분기 | ✅ 완료 | DAY_CHAT / DAY_VOTE / NIGHT_ABILITY |
| 2-4 | Fallback 처리 | ✅ 완료 | API 키 없음 or 에러 시 랜덤 폴백 |
| 2-5 | Agent 페르소나 시스템 | 🔄 확인 필요 | `persona.py` 내용 미확인 |
| 2-6 | Agent Pool 관리 | 🔄 확인 필요 | `pool.py` 내용 미확인 |
| 2-7 | 발언 타이밍 제어 | ⬜ 미구현 | 랜덤 딜레이 없음 (순차 실행) |
| 2-8 | Redis Checkpointer | ⬜ 미구현 | 멀티턴 메모리 없음 |

---

### Phase 3: WebSocket + 채팅 UI ✅ 완료 (REST 혼용)

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 3-1 | FastAPI WebSocket 엔드포인트 | ✅ 완료 | |
| 3-2 | REST API 엔드포인트 | ✅ 완료 | `/game/{id}/chat`, `/vote`, `/ability` |
| 3-3 | chat_message 처리 | ✅ 완료 | |
| 3-4 | vote 처리 | ✅ 완료 | REST POST 방식 |
| 3-5 | use_ability 처리 | ✅ 완료 | REST POST 방식, protect→heal 매핑 포함 |
| 3-6 | GameRunner 자동 시작 | ✅ 완료 | WebSocket 연결 시 asyncio.Task 자동 생성 |
| 3-7 | Streamlit 메인 레이아웃 | ✅ 완료 | `frontend/app.py` |
| 3-8 | 채팅 영역 구현 | ✅ 완료 | `chat_area.py` — 마피아 채널 탭 분리, phase별 입력 제한, 자동 스크롤 |
| 3-9 | 상태창 구현 | ✅ 완료 | `status_panel.py` — Phase별 버튼 + 타이머 JS |
| 3-10 | 플레이어 카드 | ✅ 완료 | `player_card.py` — 투표수, 사망 오버레이 등 |
| 3-11 | 로비 화면 | ✅ 완료 | `lobby.py` — player_name, game_id, player_count 저장 |
| 3-12 | 게임 화면 | 🔄 확인 필요 | `pages/game.py` 내용 미확인 |
| 3-13 | 결과 화면 | 🔄 부분 | `pages/result.py` 부분 업데이트됨 |
| 3-14 | WebSocket 이벤트 핸들러 | ✅ 완료 | `app.py` — player_death, vote_result, ability_result 처리 추가 |

---

### Phase 4: 슈퍼바이저 + A2A 연동 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 4-1 | LangGraph StateGraph 도입 | ✅ 완료 | `graph.py` — StateGraph + Node + Edge 사용 |
| 4-2 | 슈퍼바이저 → Agent 지시 흐름 | ✅ 완료 | `_issue_directives_for_phase()` → `_directive_hint_for_agent()` |
| 4-3 | 시민 슈퍼바이저 | 🔄 스켈레톤 | 첫 번째 AI 고정 타겟, trust_score 미사용 |
| 4-4 | 마피아 슈퍼바이저 | 🔄 스켈레톤 | 기본 은폐 전략만, 우선순위 로직 미구현 |
| 4-5 | 중립 슈퍼바이저 | 🔄 확인 필요 | `neutral.py` 내용 미확인 |
| 4-6 | A2A Directive 시스템 | ✅ 완료 | `directives[]` + `reports[]` GameState 연동 |
| 4-7 | Agent 보고 시스템 | 🔄 기본 | `report_to_supervisor()` MCP Tool 구현 |
| 4-8 | 슈퍼바이저 재진단 루프 | ⬜ 미구현 | Phase 종료 후 상황 재진단 없음 |
| 4-9 | Redis Checkpointer 연동 | ⬜ 미구현 | |

---

### Phase 5: RAG + MCP 통합 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 5-1 | ChromaDB RAGStore 구현 | ✅ 완료 | `rag/store.py` — PersistentClient + 임베딩 |
| 5-2 | 디스크 기반 문서 인덱싱 | ✅ 완료 | `index_from_disk()` — `.md` 자동 로드 |
| 5-3 | RAG 지식베이스 문서 | 🔄 최소 수준 | 6개 파일만 (전략 2, 발언패턴 2, 상황 1, 룰 1) |
| 5-4 | MCP Tool 구현 | ✅ 완료 | `MCPGameTools` — 전체 Tool 함수 구현 |
| 5-5 | MCP → Agent 연동 | 🔄 부분 | graph.py에서 MCPGameTools 직접 호출 (bind_tools 미사용) |
| 5-6 | RAG → Agent 프롬프트 주입 | ⬜ 미구현 | store.py 구현됐으나 player_agent에서 RAG 쿼리 없음 |
| 5-7 | 슈퍼바이저 MCP 연동 | ⬜ 미구현 | |

---

### Phase 6: 풀 게임 통합 테스트 🔄 파일 작성

> **테스트 구조**: 루트 `tests/` 폴더 없음. 백엔드/프론트 각각 보유.

| # | 작업 | 상태 | 위치 |
|---|------|------|------|
| 6-1 | 게임 엔진 단위 테스트 | 🔄 작성 | `backend/tests/test_game_engine.py` (174줄) |
| 6-2 | Agent 테스트 | 🔄 작성 | `backend/tests/test_agents.py` (41줄) |
| 6-3 | WebSocket 테스트 | 🔄 작성 | `backend/tests/test_websocket.py` (104줄) |
| 6-4 | 백엔드 pytest 설정 | ✅ 완료 | `backend/tests/conftest.py` |
| 6-5 | 프론트 E2E 테스트 | 🔄 작성 | `frontend/tests/e2e/test_lobby.py` (42줄) |
| 6-6 | 프론트 유틸 단위 테스트 | 🔄 작성 | `frontend/tests/pytest/test_utils.py` (73줄) |
| 6-7 | 전체 게임 시뮬레이션 | ⬜ 미작성 | AI vs AI 자동 실행 시나리오 |

---

### Phase 7: UI 다듬기 + 배포 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 7-1 | Docker 구성 | ✅ 완료 | |
| 7-2 | CSS 스타일링 | 🔄 구현 | `style.css` 업데이트 (낮/밤 테마 포함) |
| 7-3 | 타이머 JS 애니메이션 | ✅ 완료 | `status_panel.py` 내 JS interval 구현 |
| 7-4 | 에러 처리 유틸 | 🔄 부분 | `frontend/utils.py` `handle_request_error()` 추가 |
| 7-5 | 루트 README.md | ✅ 완료 | 추가됨 |
| 7-6 | 결과 화면 완성 | ⬜ 미완 | 직업 공개·승패 표시 미완성 |

---

## 3. 프로젝트 디렉토리 현황 (2026-03-19 기준)

```
mafia-game-web/
├── .env.example                    ✅
├── .nvmrc                          ✅
├── Dockerfile                      ✅
├── docker-compose.yml              ✅
├── requirements.txt                ✅
├── README.md                       ✅
├── ROLE_CLAUDE.md                  ✅ (루트)
├── ROLE_CURSOR.md                  ✅ (루트)
├── ROLE_GEMINI.md                  ✅ (루트)
│
├── docs/planning/                  ✅ 문서 완비
│
├── backend/
│   ├── main.py                     ✅
│   ├── websocket/ (manager, events)✅
│   ├── game/ (engine, runner, registry, snapshot, phase, timer, vote, roles, win_condition) ✅
│   ├── agents/ (graph, player_agent, persona, pool) 🔄
│   ├── supervisors/ (citizen, mafia, neutral)       🔄 스켈레톤
│   ├── rag/ (store, retriever, knowledge/)          🔄 최소 수준
│   ├── mcp/ (tools, server)        ✅
│   ├── models/ (game, chat, directive) ✅
│   └── tests/                      🔄 파일 작성
│       ├── conftest.py
│       ├── test_game_engine.py
│       ├── test_agents.py
│       └── test_websocket.py
│
├── frontend/
│   ├── app.py                      ✅
│   ├── utils.py                    ✅
│   ├── pages/
│   │   ├── lobby.py                ✅
│   │   ├── game.py                 🔄 확인 필요
│   │   └── result.py              🔄 부분 완료
│   ├── components/
│   │   ├── chat_area.py           ✅ (마피아 채널 탭 분리 완료)
│   │   ├── status_panel.py        ✅
│   │   └── player_card.py         ✅
│   ├── assets/style.css            🔄
│   └── tests/                      🔄 파일 작성
│       ├── e2e/test_lobby.py
│       └── pytest/test_utils.py
│
└── (루트 tests/ 폴더 없음 — backend/tests, frontend/tests 각각 보유)
```

---

## 4. 현재 이슈 목록 🚨

### 🔴 기획 불일치

| # | 이슈 | 조치 |
|---|------|------|
| I-1 | 투표/능력 WebSocket → REST 변경 | TECH_ARCHITECTURE 업데이트 완료 ✅ |
| I-2 | RAG → Agent 프롬프트 미연결 | Cursor: C-1 작업 |
| I-3 | MCP bind_tools 미적용 | Cursor: C-2 작업 |
| I-4 | 슈퍼바이저 전략 로직 미구현 | Cursor: C-3 작업 |
| I-5 | RAG 지식베이스 최소 수준 (6개) | Claude: 추가 문서 작성 필요 |

### 🟡 중간 이슈

| # | 이슈 | 조치 |
|---|------|------|
| I-6 | Redis Checkpointer 미연동 | Cursor: C-5 작업 |
| I-7 | 발언 타이밍 랜덤 딜레이 없음 | Cursor: C-6 작업 |
| I-8 | 마피아 밤 채팅 채널 백엔드 분리 미구현 | Cursor: C-4 작업 |
| I-9 | 결과 화면 미완성 | Gemini: G-5 작업 |

---

## 5. 최신 커밋 변경 요약

```
커밋 cca37b07 — 프론트 수정안 260319
  ✅ chat_area.py: 마피아 비밀 채널 탭 분리 구현 (G-3 완료)
                  채팅 입력 phase별 비활성화 (day_chat만 허용)
                  자동 스크롤 JS 추가
                  사망자 메시지 스타일 클래스 적용
  ✅ lobby.py: player_name, game_id, player_count session_state 저장 완성 (G-2 완료)
  ✅ app.py: player_death, vote_result, ability_result 이벤트 핸들러 추가 (G-4 대부분 완료)
  📌 ROLE_GEMINI.md 내용 일부 업데이트
```

---

## 6. 다음 우선 작업

### Claude 담당 (docs만)
```
1. RAG 지식 문서 추가 작성 (I-5)
   → backend/rag/knowledge/ 에 전략·발언패턴·상황 문서 최소 20개+ 필요
```

### Cursor 담당
```
WORK_ORDER_CURSOR.md 참조
우선순위: C-1 (RAG 연결) → C-2 (bind_tools) → C-3 (슈퍼바이저 전략) → C-4~C-7
```

### Gemini 담당
```
WORK_ORDER_GEMINI.md 참조
우선순위: G-1 (voter 필드 확인) → G-5 (결과 화면) → G-6 (CSS)
```

---

## 7. Git 커밋 규칙

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
chore: 설정, 의존성 변경
test: 테스트 추가
refactor: 리팩토링
```

## 8. 브랜치 전략

```
master  ← 현재 사용 중
dev     ← Phase 5 완성 후 분리 권장
feat/*  ← 기능별 브랜치
```
