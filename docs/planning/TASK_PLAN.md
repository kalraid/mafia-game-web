# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.2  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-18  
> **기준 커밋**: `cdf8494` (백엔드 초안)

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               🔄 스캐폴딩 완료 / 구현 확인 필요
Phase 2: AI Agent 기초                🔄 스캐폴딩 완료 / 구현 확인 필요
Phase 3: WebSocket + 채팅 UI          🔄 스캐폴딩 완료 / 구현 확인 필요
Phase 4: 슈퍼바이저 + A2A 연동        🔄 스캐폴딩 완료 / 구현 확인 필요
Phase 5: RAG + MCP 통합               ⬜ 미시작
Phase 6: 풀 게임 통합 테스트          ⬜ 미시작
Phase 7: UI 다듬기 + 배포             🔄 Docker 파일 존재 / 나머지 미구현
```

> **스캐폴딩 완료**: 파일/폴더 구조는 생성됐으나 실제 로직 구현 내용 확인 필요

---

## 2. 작업 항목 상세

### Phase 0: 환경 구성 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 0-1 | 프로젝트 구조 생성 | ✅ 완료 | 전체 디렉토리 구조 생성됨 |
| 0-2 | 의존성 정의 | ✅ 완료 | `requirements.txt` 존재 |
| 0-3 | Git 저장소 초기화 | ✅ 완료 | origin/master 연결됨 |
| 0-4 | 환경변수 설계 | ✅ 완료 | `.env.example` 존재 |
| 0-5 | Docker 구성 | ✅ 완료 | `Dockerfile`, `docker-compose.yml` 존재 |

---

### Phase 1: 게임 엔진 코어 🔄 스캐폴딩 완료

| # | 작업 | 상태 | 파일 | 비고 |
|---|------|------|------|------|
| 1-1 | 데이터 모델 정의 | 🔄 확인 필요 | `backend/models/game.py`, `chat.py`, `directive.py` | |
| 1-2 | Phase Manager | 🔄 확인 필요 | `backend/game/phase.py` | |
| 1-3 | 타이머 시스템 | 🔄 확인 필요 | `backend/game/timer.py` | |
| 1-4 | 직업 배분 로직 | 🔄 확인 필요 | `backend/game/roles.py` | |
| 1-5 | 투표 시스템 | 🔄 확인 필요 | `backend/game/vote.py` | |
| 1-6 | 직업 능력 처리 | 🔄 확인 필요 | `backend/game/roles.py` | |
| 1-7 | 승리 조건 판정 | 🔄 확인 필요 | `backend/game/win_condition.py` | |
| 1-8 | 게임 엔진 코어 | 🔄 확인 필요 | `backend/game/engine.py` | |
| 1-9 | 게임 로그 | ⬜ 미구현 | — | Phase 1 완료 후 추가 |

---

### Phase 2: AI Agent 기초 🔄 스캐폴딩 완료

| # | 작업 | 상태 | 파일 | 비고 |
|---|------|------|------|------|
| 2-1 | 단일 Agent LangGraph 노드 | 🔄 확인 필요 | `backend/agents/player_agent.py` | bind_tools + ToolNode 패턴 필수 |
| 2-2 | Agent 페르소나 시스템 | 🔄 확인 필요 | `backend/agents/persona.py` | |
| 2-3 | 발언 생성 프롬프트 | 🔄 확인 필요 | `backend/agents/player_agent.py` | |
| 2-4 | 투표 결정 로직 | 🔄 확인 필요 | `backend/agents/player_agent.py` | |
| 2-5 | 밤 능력 결정 로직 | 🔄 확인 필요 | `backend/agents/player_agent.py` | |
| 2-6 | Agent Pool 관리 | 🔄 확인 필요 | `backend/agents/pool.py` | |
| 2-7 | LangGraph Main Graph | 🔄 확인 필요 | `backend/agents/graph.py` | |
| 2-8 | 발언 타이밍 제어 | ⬜ 미구현 | — | 랜덤 딜레이 + 성격 가중치 |
| 2-9 | Redis Checkpointer 연동 | ⬜ 미구현 | — | 멀티턴 메모리 필수 |

---

### Phase 3: WebSocket + 채팅 UI 🔄 스캐폴딩 완료

| # | 작업 | 상태 | 파일 | 비고 |
|---|------|------|------|------|
| 3-1 | FastAPI WebSocket 엔드포인트 | 🔄 확인 필요 | `backend/websocket/manager.py` | |
| 3-2 | WebSocket 이벤트 처리 | 🔄 확인 필요 | `backend/websocket/events.py` | |
| 3-3 | 브로드캐스트 시스템 | 🔄 확인 필요 | `backend/websocket/manager.py` | |
| 3-4 | FastAPI 진입점 | 🔄 확인 필요 | `backend/main.py` | |
| 3-5 | Streamlit 메인 레이아웃 | 🔄 확인 필요 | `frontend/app.py` | |
| 3-6 | 채팅 영역 구현 | 🔄 확인 필요 | `frontend/components/chat_area.py` | |
| 3-7 | 상태창 구현 | 🔄 확인 필요 | `frontend/components/status_panel.py` | |
| 3-8 | 플레이어 카드 | 🔄 확인 필요 | `frontend/components/player_card.py` | |
| 3-9 | 사망 오버레이 CSS | 🔄 확인 필요 | `frontend/assets/style.css` | |
| 3-10 | 로비 화면 | 🔄 확인 필요 | `frontend/pages/lobby.py` | |
| 3-11 | 게임 화면 | 🔄 확인 필요 | `frontend/pages/game.py` | |
| 3-12 | 게임 종료 화면 | 🔄 확인 필요 | `frontend/pages/result.py` | |

---

### Phase 4: 슈퍼바이저 + A2A 연동 🔄 스캐폴딩 완료

| # | 작업 | 상태 | 파일 | 비고 |
|---|------|------|------|------|
| 4-1 | 시민 슈퍼바이저 | 🔄 확인 필요 | `backend/supervisors/citizen.py` | |
| 4-2 | 마피아 슈퍼바이저 | 🔄 확인 필요 | `backend/supervisors/mafia.py` | |
| 4-3 | 중립 슈퍼바이저 | 🔄 확인 필요 | `backend/supervisors/neutral.py` | |
| 4-4 | A2A Directive 시스템 | 🔄 확인 필요 | `backend/models/directive.py` | |
| 4-5 | Agent 보고 시스템 | 🔄 확인 필요 | — | directive.py 내 포함 여부 확인 |
| 4-6 | LangGraph 슈퍼바이저 통합 | 🔄 확인 필요 | `backend/agents/graph.py` | |
| 4-7 | 슈퍼바이저 재진단 루프 | ⬜ 미구현 | — | 평가 반영: 파이프라인 방지 |

---

### Phase 5: RAG + MCP 통합 ⬜ 미시작

| # | 작업 | 상태 | 파일 | 담당 |
|---|------|------|------|------|
| 5-1 | RAG 지식베이스 문서 작성 | ⬜ 미시작 | `rag/knowledge/` (폴더 없음) | Claude |
| 5-2 | ChromaDB 셋업 | ⬜ 미시작 | `backend/rag/store.py` (파일만) | Cursor |
| 5-3 | RAG 검색 파이프라인 | ⬜ 미시작 | `backend/rag/retriever.py` (파일만) | Cursor |
| 5-4 | MCP Tool 서버 구현 | ⬜ 미시작 | `backend/mcp/tools.py`, `server.py` (파일만) | Cursor |
| 5-5 | Agent에 MCP 연동 | ⬜ 미시작 | `backend/agents/player_agent.py` | Cursor |
| 5-6 | 슈퍼바이저 MCP 연동 | ⬜ 미시작 | — | Cursor |

---

### Phase 6: 풀 게임 통합 테스트 ⬜ 미시작

| # | 작업 | 상태 | 파일 | 비고 |
|---|------|------|------|------|
| 6-1 | 단위 테스트 | ⬜ 미시작 | `tests/test_game_engine.py` (파일만) | |
| 6-2 | Agent 발언 품질 테스트 | ⬜ 미시작 | `tests/test_agents.py` (파일만) | |
| 6-3 | WebSocket 테스트 | ⬜ 미시작 | `tests/test_websocket.py` (파일만) | |
| 6-4 | 전체 게임 시뮬레이션 | ⬜ 미시작 | — | AI vs AI 자동 실행 |
| 6-5 | 사람 참여 통합 테스트 | ⬜ 미시작 | — | |
| 6-6 | 승리 조건 엣지 케이스 | ⬜ 미시작 | — | |

---

### Phase 7: UI 다듬기 + 배포 🔄 부분 완료

| # | 작업 | 상태 | 파일 | 비고 |
|---|------|------|------|------|
| 7-1 | Docker 구성 | ✅ 완료 | `Dockerfile`, `docker-compose.yml` | |
| 7-2 | CSS 스타일링 | 🔄 확인 필요 | `frontend/assets/style.css` | |
| 7-3 | 타이머 애니메이션 | ⬜ 미구현 | — | |
| 7-4 | 에러 처리 | ⬜ 미구현 | — | except:pass 금지, 로깅 필수 |
| 7-5 | 루트 README.md | ⬜ 미구현 | — | 실행 방법 문서 |

---

## 3. 현재 이슈 목록 🚨

| # | 이슈 | 위치 | 조치 |
|---|------|------|------|
| I-1 | `ROLE_CLUDE.md` 오타 | 루트 | `ROLE_CLAUDE.md`로 rename (루트 유지) |
| I-2 | `backend/rag/knowledge/` 폴더 없음 | backend/rag | Phase 5 시작 전 생성 |
| I-3 | 루트 `README.md` 없음 | 루트 | Phase 7에서 작성 |

### I-1 즉시 조치 (PowerShell)

```powershell
cd C:\Users\INSoft\.git\mafia-game-web
git mv ROLE_CLUDE.md ROLE_CLAUDE.md
git commit -m "fix: rename ROLE_CLUDE.md to ROLE_CLAUDE.md (typo)"
git push origin master
```

---

## 4. 실제 프로젝트 디렉토리 현황 (2026-03-18 기준)

```
mafia-game-web/                     (master, 커밋 2개)
├── .env.example                    ✅
├── Dockerfile                      ✅
├── docker-compose.yml              ✅
├── requirements.txt                ✅
├── README.md                       ❌ 없음 (Phase 7)
├── ROLE_CLUDE.md                   ⚠️ 오타 → rename 필요
├── ROLE_CURSOR.md                  ✅ (루트 유지)
├── ROLE_GEMINI.md                  ✅ (루트 유지)
│
├── docs/planning/                  ✅ 문서 완비
│
├── backend/                        🔄 스캐폴딩 완료
│   ├── main.py
│   ├── websocket/ (manager, events)
│   ├── game/ (engine, phase, timer, vote, roles, win_condition)
│   ├── agents/ (graph, player_agent, persona, pool)
│   ├── supervisors/ (citizen, mafia, neutral)
│   ├── rag/ (store, retriever)
│   ├── rag/knowledge/              ❌ 폴더 없음 (Phase 5)
│   ├── mcp/ (tools, server)
│   └── models/ (game, chat, directive)
│
├── frontend/                       🔄 스캐폴딩 완료
│   ├── app.py
│   ├── pages/ (lobby, game, result)
│   ├── components/ (chat_area, status_panel, player_card)
│   └── assets/style.css
│
└── tests/                          ⬜ 파일만 존재
    ├── test_game_engine.py
    ├── test_agents.py
    └── test_websocket.py
```

---

## 5. 다음 액션

```
즉시:
  1. ROLE_CLUDE.md → ROLE_CLAUDE.md rename 후 push
  2. 업데이트된 문서들 push

다음 단계:
  3. 스캐폴딩된 파일 실제 구현 내용 Claude에게 공유 (검토)
  4. Phase 1 → 2 → 3 순서로 구현 완성
```

---

## 6. Git 커밋 규칙

```
feat: 새 기능 추가
fix: 버그 수정 / 오타 수정
docs: 문서 수정
chore: 설정, 의존성 변경
test: 테스트 추가
refactor: 리팩토링
```

## 7. 브랜치 전략

```
master        ← 현재 사용 중 (초기 단계 단일 브랜치)
dev           ← Phase 3 이후 분리 권장
feat/*        ← 기능별 브랜치
```
