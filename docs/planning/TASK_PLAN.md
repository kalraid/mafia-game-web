# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.3  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-18  
> **기준**: GitHub 실제 코드 직접 리뷰 결과 반영

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               🔄 부분 구현 (vote 완성, roles 스켈레톤)
Phase 2: AI Agent 기초                🔄 스켈레톤 (LLM 미연동)
Phase 3: WebSocket + 채팅 UI          🔄 기본 동작 (chat echo만)
Phase 4: 슈퍼바이저 + A2A 연동        🔄 스켈레톤 (전략 로직 없음)
Phase 5: RAG + MCP 통합               ⬜ 미시작 (빈 파일만)
Phase 6: 풀 게임 통합 테스트          ⬜ 미시작
Phase 7: UI 다듬기 + 배포             🔄 Docker 완료 / UI 미확인
```

---

## 2. 작업 항목 상세

### Phase 0: 환경 구성 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 0-1 | 프로젝트 구조 생성 | ✅ 완료 | 전체 디렉토리 구조 생성 |
| 0-2 | 의존성 정의 | ✅ 완료 | `requirements.txt` — redis, langchain, chromadb 등 포함 |
| 0-3 | Git 저장소 초기화 | ✅ 완료 | origin/master 연결됨 |
| 0-4 | 환경변수 설계 | ✅ 완료 | `.env.example` 존재 |
| 0-5 | Docker 구성 | ✅ 완료 | `Dockerfile`, `docker-compose.yml` 존재 |

---

### Phase 1: 게임 엔진 코어 🔄 부분 구현

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 1-1 | 데이터 모델 정의 | ✅ 완료 | `models/game.py` — Role/Phase/Player/GameState/directives/reports 완성 |
| 1-2 | Phase Manager | 🔄 확인 필요 | `game/phase.py` 존재, 내용 미확인 |
| 1-3 | 타이머 시스템 | 🔄 확인 필요 | `game/timer.py` 존재, 내용 미확인 |
| 1-4 | 직업 배분 로직 | 🔄 확인 필요 | `game/roles.py` 내 배분 로직 여부 미확인 |
| 1-5 | 투표 시스템 | ✅ 완료 | `game/vote.py` — tally_votes 구현 (동률 처리 포함) |
| 1-6 | 직업 능력 처리 | 🔄 스켈레톤 | `game/roles.py` — 함수 시그니처만, 실제 로직 없음 |
| 1-7 | 승리 조건 판정 | 🔄 확인 필요 | `game/win_condition.py` 존재, 내용 미확인 |
| 1-8 | 게임 엔진 코어 | 🔄 기본 구현 | `game/engine.py` — Phase 전환 + 승리 조건 체크 연결 |
| 1-9 | 게임 로그 | ⬜ 미구현 | `GameEvent` 모델은 있으나 실제 로깅 없음 |

---

### Phase 2: AI Agent 기초 🔄 스켈레톤 (LLM 미연동)

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 2-1 | 단일 Agent LangGraph 노드 | 🔄 스켈레톤 | `player_agent.py` — `run()` 항상 None 반환, LLM 미연동 |
| 2-2 | Agent 페르소나 시스템 | 🔄 확인 필요 | `persona.py` 존재, 내용 미확인 |
| 2-3 | 발언 생성 프롬프트 | ⬜ 미구현 | LLM 연동 전 구현 불가 |
| 2-4 | 투표 결정 로직 | ⬜ 미구현 | LLM 연동 전 구현 불가 |
| 2-5 | 밤 능력 결정 로직 | ⬜ 미구현 | LLM 연동 전 구현 불가 |
| 2-6 | Agent Pool 관리 | 🔄 확인 필요 | `pool.py` 존재, 내용 미확인 |
| 2-7 | LangGraph Main Graph | 🔄 스켈레톤 | `graph.py` — LangGraph 미사용, 직접 async 호출 |
| 2-8 | 발언 타이밍 제어 | ⬜ 미구현 | 랜덤 딜레이 + 성격 가중치 |
| 2-9 | Redis Checkpointer 연동 | ⬜ 미구현 | 멀티턴 메모리 필수 |

> ⚠️ **핵심 미구현**: `player_agent.py`의 `run()` 메서드가 항상 `None`을 반환합니다.
> LangChain + Claude API 실제 연동이 Phase 2의 최우선 작업입니다.

---

### Phase 3: WebSocket + 채팅 UI 🔄 기본 동작

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 3-1 | FastAPI WebSocket 엔드포인트 | ✅ 완료 | `main.py` — `/ws/{game_id}` 구현 |
| 3-2 | WebSocket 이벤트 처리 | 🔄 부분 구현 | `manager.py` — chat_message echo만, vote/ability 미처리 |
| 3-3 | 브로드캐스트 시스템 | ✅ 완료 | `manager.py` — broadcast 구현 |
| 3-4 | FastAPI 진입점 | ✅ 완료 | `main.py` — health check + ws 엔드포인트 |
| 3-5 | Streamlit 메인 레이아웃 | 🔄 기본 구현 | `frontend/app.py` — WebSocket 연결 + 페이지 라우팅 |
| 3-6 | 채팅 영역 구현 | 🔄 확인 필요 | `components/chat_area.py` 내용 미확인 |
| 3-7 | 상태창 구현 | 🔄 확인 필요 | `components/status_panel.py` 내용 미확인 |
| 3-8 | 플레이어 카드 | 🔄 확인 필요 | `components/player_card.py` 내용 미확인 |
| 3-9 | 사망 오버레이 CSS | 🔄 확인 필요 | `assets/style.css` 내용 미확인 |
| 3-10 | 로비 화면 | 🔄 확인 필요 | `pages/lobby.py` 내용 미확인 |
| 3-11 | 게임 화면 | 🔄 확인 필요 | `pages/game.py` 내용 미확인 |
| 3-12 | 게임 종료 화면 | 🔄 확인 필요 | `pages/result.py` 내용 미확인 |
| 3-13 | vote/ability WebSocket 핸들러 | ⬜ 미구현 | `manager.py`에 chat_message만 처리 중 |

---

### Phase 4: 슈퍼바이저 + A2A 연동 🔄 스켈레톤

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 4-1 | 시민 슈퍼바이저 | 🔄 확인 필요 | `supervisors/citizen.py` 내용 미확인 |
| 4-2 | 마피아 슈퍼바이저 | 🔄 스켈레톤 | `supervisors/mafia.py` — 첫번째 시민만 타겟, 전략 없음 |
| 4-3 | 중립 슈퍼바이저 | 🔄 확인 필요 | `supervisors/neutral.py` 내용 미확인 |
| 4-4 | A2A Directive 시스템 | 🔄 모델만 | `models/directive.py` — Directive/Report 모델은 있음 |
| 4-5 | Agent 보고 시스템 | ⬜ 미구현 | 모델은 있으나 실제 보고 흐름 없음 |
| 4-6 | LangGraph 슈퍼바이저 통합 | ⬜ 미구현 | graph.py가 LangGraph 미사용 |
| 4-7 | 슈퍼바이저 재진단 루프 | ⬜ 미구현 | 평가 반영 필수 항목 |

---

### Phase 5: RAG + MCP 통합 ⬜ 미시작

| # | 작업 | 상태 | 담당 |
|---|------|------|------|
| 5-1 | RAG 지식베이스 문서 작성 | ⬜ 미시작 | Claude |
| 5-2 | ChromaDB 셋업 | ⬜ 미시작 | Cursor (rag/store.py 빈 파일) |
| 5-3 | RAG 검색 파이프라인 | ⬜ 미시작 | Cursor (rag/retriever.py 빈 파일) |
| 5-4 | MCP Tool 서버 구현 | ⬜ 미시작 | Cursor (mcp/tools.py, server.py 빈 파일) |
| 5-5 | Agent에 MCP 연동 | ⬜ 미시작 | Cursor |
| 5-6 | 슈퍼바이저 MCP 연동 | ⬜ 미시작 | Cursor |

---

### Phase 6: 풀 게임 통합 테스트 ⬜ 미시작

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 6-1 | 단위 테스트 | ⬜ 미시작 | `tests/*.py` 파일만 존재 |
| 6-2 | Agent 발언 품질 테스트 | ⬜ 미시작 | Phase 2 완료 후 가능 |
| 6-3 | 전체 게임 시뮬레이션 | ⬜ 미시작 | |
| 6-4 | 사람 참여 통합 테스트 | ⬜ 미시작 | |

---

### Phase 7: UI 다듬기 + 배포 🔄 부분

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 7-1 | Docker 구성 | ✅ 완료 | Dockerfile, docker-compose.yml |
| 7-2 | CSS 스타일링 | 🔄 확인 필요 | style.css 존재, 내용 미확인 |
| 7-3 | 타이머 애니메이션 | ⬜ 미구현 | |
| 7-4 | 에러 처리 | ⬜ 미구현 | |
| 7-5 | 루트 README.md | ⬜ 미구현 | 실행 방법 문서 없음 |

---

## 3. 현재 이슈 목록 🚨

| # | 이슈 | 심각도 | 조치 |
|---|------|--------|------|
| I-1 | `player_agent.py`의 `run()` 항상 None 반환 | 🔴 높음 | LLM 연동 구현 필요 (Phase 2 핵심) |
| I-2 | `graph.py`가 LangGraph 미사용 | 🔴 높음 | 실제 LangGraph 노드/엣지로 교체 필요 |
| I-3 | `websocket/manager.py` vote/ability 이벤트 미처리 | 🔴 높음 | Phase 3 완성 위해 필수 |
| I-4 | `game/roles.py` 능력 함수 로직 없음 | 🟡 중간 | Phase 1 완성 위해 필요 |
| I-5 | `supervisors/mafia.py` 단순 첫번째 시민 타겟팅 | 🟡 중간 | 전략 로직 추가 필요 |
| I-6 | `streamlit-websocket-client==0.0.1` 패키지 검증 필요 | 🟡 중간 | 실제 PyPI 존재 여부 확인 필요 |
| I-7 | Redis Checkpointer 미연동 | 🟡 중간 | Phase 2 구현 시 병행 필요 |
| I-8 | 루트 README.md 없음 | 🟢 낮음 | Phase 7에서 작성 |

---

## 4. 실제 코드 리뷰 결과 요약 (2026-03-18)

```
✅ 완성된 것:
  - models/game.py (GameState, Player, Role, Phase, directives, reports)
  - game/vote.py (tally_votes, 동률 처리)
  - game/engine.py (Phase 전환 기본 동작)
  - websocket/manager.py (connect/disconnect/broadcast)
  - backend/main.py (FastAPI + WebSocket 엔드포인트)
  - frontend/app.py (WebSocket 연결 + 페이지 라우팅)
  - requirements.txt (redis, langchain, chromadb 등 포함)

🔄 스켈레톤 (구조만, 실제 동작 없음):
  - player_agent.py (run() → 항상 None)
  - agents/graph.py (LangGraph 아님, 직접 async 호출)
  - game/roles.py (능력 함수 시그니처만)
  - supervisors/mafia.py (첫번째 시민 타겟팅만)

⬜ 빈 파일:
  - rag/store.py, rag/retriever.py
  - mcp/tools.py, mcp/server.py
  - tests/*.py
```

---

## 5. 다음 우선 작업 (Cursor 지시)

```
우선순위 1: Phase 2 — LLM 실제 연동
  → player_agent.py에 LangChain + Claude API 연동
  → bind_tools + ToolNode 패턴 (EVALUATION_REFLECTION.md 참조)
  → Redis Checkpointer 연동 (RAG_AND_STORAGE_DESIGN.md 참조)

우선순위 2: Phase 1 완성
  → game/roles.py 능력 로직 구현 (detective, doctor, mafia, killer)

우선순위 3: Phase 3 완성
  → websocket/manager.py에 vote, use_ability 이벤트 핸들러 추가
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
dev     ← Phase 3 이후 분리 권장
feat/*  ← 기능별 브랜치
```
