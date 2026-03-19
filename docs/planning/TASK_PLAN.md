# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.5  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-19  
> **기준 커밋**: `978c755` (test 파일 위치 이동)

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               ✅ 완료 (vote, ability, engine, runner, snapshot)
Phase 2: AI Agent 기초                ✅ 완료 (LLM 연동, Structured Output, Fallback)
Phase 3: WebSocket + 채팅 UI          ✅ 완료 (REST API 방식 혼용)
Phase 4: 슈퍼바이저 + A2A 연동        🔄 부분 완료 (LangGraph 도입, 전략 로직 미완)
Phase 5: RAG + MCP 통합               🔄 부분 완료 (ChromaDB 구현, 지식베이스 최소 수준)
Phase 6: 풀 게임 통합 테스트          🔄 테스트 파일 작성 (실행 여부 미확인)
Phase 7: UI 다듬기 + 배포             🔄 CSS·컴포넌트 구현 완료, 에러 처리 미완
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
| 3-2 | REST API 엔드포인트 | ✅ 완료 | `/game/{id}/chat`, `/vote`, `/ability` 추가 |
| 3-3 | chat_message 처리 | ✅ 완료 | |
| 3-4 | vote 처리 | ✅ 완료 | REST POST 방식으로 변경 |
| 3-5 | use_ability 처리 | ✅ 완료 | REST POST 방식, protect→heal 매핑 포함 |
| 3-6 | GameRunner 자동 시작 | ✅ 완료 | WebSocket 연결 시 asyncio.Task 자동 생성 |
| 3-7 | Streamlit 메인 레이아웃 | ✅ 완료 | `frontend/app.py` |
| 3-8 | 채팅 영역 구현 | 🔄 확인 필요 | `chat_area.py` 업데이트됨 |
| 3-9 | 상태창 구현 | ✅ 완료 | `status_panel.py` — Phase별 버튼 + 타이머 JS |
| 3-10 | 플레이어 카드 | ✅ 완료 | `player_card.py` — 투표수, 사망 오버레이 등 |
| 3-11 | 로비/게임/결과 화면 | 🔄 확인 필요 | `pages/*.py` 부분 업데이트됨 |

---

### Phase 4: 슈퍼바이저 + A2A 연동 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 4-1 | LangGraph StateGraph 도입 | ✅ 완료 | `graph.py` — StateGraph + Node + Edge 사용 |
| 4-2 | 슈퍼바이저 → Agent 지시 흐름 | ✅ 완료 | `_issue_directives_for_phase()` → `_directive_hint_for_agent()` |
| 4-3 | 시민 슈퍼바이저 | 🔄 스켈레톤 | 첫 번째 AI를 의심 대상으로 고정, trust_score 미사용 |
| 4-4 | 마피아 슈퍼바이저 | 🔄 스켈레톤 | 기본 은폐 전략만, 우선순위 로직 미구현 |
| 4-5 | 중립 슈퍼바이저 | 🔄 스켈레톤 | `neutral.py` 내용 미확인 |
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

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 6-1 | 게임 엔진 단위 테스트 | 🔄 작성 | `backend/tests/test_game_engine.py` (174줄) |
| 6-2 | Agent 테스트 | 🔄 작성 | `backend/tests/test_agents.py` (41줄) |
| 6-3 | WebSocket 테스트 | 🔄 작성 | `backend/tests/test_websocket.py` (104줄) |
| 6-4 | 프론트 E2E 테스트 | 🔄 작성 | `frontend/tests/e2e/test_lobby.py` (42줄) |
| 6-5 | 유틸 단위 테스트 | 🔄 작성 | `frontend/tests/pytest/test_utils.py` (73줄) |
| 6-6 | 전체 게임 시뮬레이션 | ⬜ 미작성 | AI vs AI 자동 실행 시나리오 |

---

### Phase 7: UI 다듬기 + 배포 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 7-1 | Docker 구성 | ✅ 완료 | |
| 7-2 | CSS 스타일링 | 🔄 구현 | `style.css` 업데이트 (낮/밤 테마 포함) |
| 7-3 | 타이머 JS 애니메이션 | ✅ 완료 | `status_panel.py` 내 JS interval 구현 |
| 7-4 | 에러 처리 유틸 | 🔄 부분 | `frontend/utils.py` `handle_request_error()` 추가 |
| 7-5 | 루트 README.md | ✅ 완료 | 추가됨 |

---

## 3. 현재 이슈 목록 🚨

### 🔴 기획 불일치 (설계 vs 구현)

| # | 이슈 | 설명 | 조치 필요 |
|---|------|------|----------|
| I-1 | **투표/능력 WebSocket → REST 변경** | UI_DESIGN·TECH_ARCHITECTURE는 WebSocket 방식으로 설계했으나 프론트가 REST POST로 구현 | TECH_ARCHITECTURE 업데이트 or 프론트 방식 통일 결정 필요 |
| I-2 | **RAG → Agent 프롬프트 미연결** | `rag/store.py` 구현됐으나 `player_agent.py`에서 RAG 쿼리 없음 | Cursor: player_agent의 `_decide_with_llm`에 RAG 컨텍스트 주입 |
| I-3 | **MCP bind_tools 미적용** | EVALUATION_REFLECTION 기준 `bind_tools+ToolNode` 패턴 필수인데 MCPGameTools 직접 호출 중 | Cursor: LLM.bind_tools() 패턴으로 전환 |
| I-4 | **슈퍼바이저 전략 로직 미구현** | 첫 번째 AI를 의심 대상으로 고정, trust_score 미사용 | Cursor: Phase 4 전략 로직 고도화 필요 |
| I-5 | **RAG 지식베이스 최소 수준** | 6개 파일 (평가 기준 미달) | Claude: 추가 지식 문서 작성 필요 (Phase 5-1) |

### 🟡 중간 이슈

| # | 이슈 | 조치 |
|---|------|------|
| I-6 | Redis Checkpointer 미연동 | 멀티턴 메모리 없음, Phase 4 완성 전 필요 |
| I-7 | 발언 타이밍 랜덤 딜레이 없음 | 자연스러운 AI 발화 위해 필요 |
| I-8 | 마피아 밤 채팅 채널 분리 미구현 | TECH_ARCHITECTURE: `mafia_secret` 채널 없음 |
| I-9 | `persona.py`, `pool.py` 내용 미확인 | 페르소나 실제 활용 여부 불명 |

---

## 4. 최신 커밋 변경 요약 (2026-03-19)

```
커밋 978c755 — test 파일 위치 이동
  tests/*.py → backend/tests/*.py 이동 (파일 삭제됨, backend/tests에 재생성)

커밋 6a6086d — 프론트엔드 초안
  ✅ status_panel.py: Phase별 버튼 + 타이머 JS + 플레이어 목록 완성
  ✅ player_card.py: 투표 수, 사망 오버레이, 클릭 선택 구현
  ✅ chat_area.py: 채팅 표시 업데이트
  ✅ frontend/utils.py: handle_request_error 유틸 추가
  ✅ frontend/tests/: E2E + 단위 테스트 추가
  ⚠️ 투표/능력을 WebSocket 아닌 REST POST로 구현 (설계 변경)

커밋 9e735ac — 백엔드 초안 작성
  ✅ graph.py: LangGraph StateGraph 실제 도입 (Node/Edge 구조)
  ✅ runner.py: GameRunner — asyncio 기반 게임 루프 완성
  ✅ snapshot.py: 게임 상태 payload 빌드 유틸
  ✅ main.py: REST API (/chat, /vote, /ability) + GameRunner 자동 시작
  ✅ rag/store.py: ChromaDB + sentence-transformers RAG 구현
  ✅ rag/knowledge/: 6개 지식 문서 추가 (최소 수준)
  ✅ mcp/tools.py: MCPGameTools 전체 Tool 구현
  ✅ supervisors/: 3개 슈퍼바이저 업데이트 (스켈레톤 수준)
  ✅ backend/tests/: 테스트 파일 이동 및 추가
```

---

## 5. 다음 우선 작업

### Claude 담당 (docs만)
```
1. RAG 지식 문서 추가 작성 (Phase 5-1)
   → rag/knowledge/ 에 전략·발언패턴·상황 문서 최소 20개+ 필요
2. TECH_ARCHITECTURE 업데이트
   → 투표/능력 REST 방식 반영 (WebSocket → REST 설계 변경 기록)
3. 기획 불일치 이슈 (I-1~I-5) Cursor에게 작업 지시
```

### Cursor 담당 (백엔드)
```
1. player_agent.py에 RAG 컨텍스트 주입 (I-2)
2. 슈퍼바이저 전략 로직 고도화 — trust_score 기반 (I-4)
3. 마피아 밤 채팅 채널 mafia_secret 분리 (I-8)
4. 발언 타이밍 랜덤 딜레이 추가 (I-7)
5. Redis Checkpointer 연동 (I-6)
```

### Gemini 담당 (프론트)
```
1. REST POST voter 필드 sender → player_name 통일 확인
2. 마피아 밤 채팅 채널 분리 UI 반영
3. 로비 화면 완성 (game_id, player_name, player_count 입력)
```

---

## 6. Git 커밋 규칙

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
chore: 설정, 의존성 변경
test: 테스트 추가
refactor: 리팩토링
```

## 7. 브랜치 전략

```
master  ← 현재 사용 중
dev     ← Phase 5 완성 후 분리 권장
feat/*  ← 기능별 브랜치
```
