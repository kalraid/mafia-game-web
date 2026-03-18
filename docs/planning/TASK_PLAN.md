# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.0  
> **작성일**: 2026-03-18

---

## 1. 개발 단계 개요

```
Phase 0: 환경 구성 & 기반 작업
Phase 1: 게임 엔진 코어 (룰, 상태 관리)
Phase 2: AI Agent 기초 (단일 Agent 동작)
Phase 3: WebSocket + 채팅 UI
Phase 4: 슈퍼바이저 + A2A 연동
Phase 5: RAG + MCP 통합
Phase 6: 풀 게임 통합 테스트
Phase 7: UI 다듬기 + 배포
```

---

## 2. 작업 항목 상세 (우선순위 순)

### Phase 0: 환경 구성 (1~2일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 0-1 | 프로젝트 구조 생성 | 디렉토리, pyproject.toml, .env | 🔴 필수 |
| 0-2 | 의존성 정의 | requirements.txt (FastAPI, LangChain, LangGraph 등) | 🔴 필수 |
| 0-3 | Git 저장소 초기화 | .gitignore, 브랜치 전략 | 🔴 필수 |
| 0-4 | 환경변수 설계 | API 키, 서버 설정값 | 🔴 필수 |

---

### Phase 1: 게임 엔진 코어 (3~5일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 1-1 | 데이터 모델 정의 | GameState, Player, Role, ChatMessage (Pydantic) | 🔴 필수 |
| 1-2 | Phase Manager | 낮/밤/투표 Phase 전환 로직 | 🔴 필수 |
| 1-3 | 타이머 시스템 | asyncio 기반 Phase 타이머 | 🔴 필수 |
| 1-4 | 직업 배분 로직 | 인원 수 → 직업 자동 배분 | 🔴 필수 |
| 1-5 | 투표 시스템 | 투표 집계, 동률 처리, 처형 로직 | 🔴 필수 |
| 1-6 | 직업 능력 처리 | 경찰/의사/마피아/킬러 능력 로직 | 🔴 필수 |
| 1-7 | 승리 조건 판정 | 시민승리/마피아승리/광대승리 자동 체크 | 🔴 필수 |
| 1-8 | 게임 로그 | 이벤트 로깅 시스템 | 🟡 권장 |

---

### Phase 2: AI Agent 기초 (5~7일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 2-1 | 단일 Agent LangGraph 노드 구현 | 입력 → 추론 → 발언 출력 기본 흐름 | 🔴 필수 |
| 2-2 | Agent 페르소나 시스템 | 이름, 말투, 성격 속성 부여 | 🔴 필수 |
| 2-3 | 발언 생성 프롬프트 설계 | 직업별 시스템 프롬프트 | 🔴 필수 |
| 2-4 | 투표 결정 로직 | trust_score 기반 투표 대상 선택 | 🔴 필수 |
| 2-5 | 밤 능력 결정 로직 | 직업별 능력 사용 대상 결정 | 🔴 필수 |
| 2-6 | Agent Pool 관리 | 19개 Agent 인스턴스 생성/관리 | 🔴 필수 |
| 2-7 | 발언 타이밍 제어 | 랜덤 딜레이 + 성격별 가중치 | 🟡 권장 |

---

### Phase 3: WebSocket + 채팅 UI (3~5일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 3-1 | FastAPI WebSocket 엔드포인트 | /ws/{game_id} 연결 관리 | 🔴 필수 |
| 3-2 | WebSocket 이벤트 처리 | chat_message, vote, use_ability 수신 | 🔴 필수 |
| 3-3 | 브로드캐스트 시스템 | 채널별 메시지 필터링 후 전달 | 🔴 필수 |
| 3-4 | Streamlit 메인 레이아웃 | 3/4 채팅 + 1/4 상태창 구조 | 🔴 필수 |
| 3-5 | 채팅 영역 구현 | 메시지 표시, 입력창, 전송 | 🔴 필수 |
| 3-6 | 상태창 구현 | 밤낮 표시, 플레이어 목록, 버튼 | 🔴 필수 |
| 3-7 | 사망 오버레이 | 검은 천 CSS 효과 | 🟡 권장 |
| 3-8 | 로비 화면 | 닉네임 입력, 인원 설정 | 🔴 필수 |
| 3-9 | 게임 종료 화면 | 승패 결과, 직업 공개 | 🟡 권장 |

---

### Phase 4: 슈퍼바이저 + A2A 연동 (4~6일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 4-1 | 시민 슈퍼바이저 구현 | 전략 수립, 지시 생성 | 🔴 필수 |
| 4-2 | 마피아 슈퍼바이저 구현 | 공격 대상 결정, 은폐 전략 | 🔴 필수 |
| 4-3 | 중립 슈퍼바이저 구현 | 광대/스파이 목표 달성 지원 | 🟡 권장 |
| 4-4 | A2A Directive 시스템 | GameState.directives 채널 구현 | 🔴 필수 |
| 4-5 | Agent 보고 시스템 | Agent → 슈퍼바이저 정보 전달 | 🔴 필수 |
| 4-6 | LangGraph Main Graph | Phase별 서브그래프 오케스트레이션 | 🔴 필수 |
| 4-7 | 슈퍼바이저 실행 타이밍 | Phase 전환 시점에 슈퍼바이저 실행 | 🔴 필수 |

---

### Phase 5: RAG + MCP 통합 (3~4일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 5-1 | RAG 지식베이스 구축 | 마피아 전략 문서 작성 및 임베딩 | 🔴 필수 |
| 5-2 | ChromaDB 셋업 | 벡터 DB 초기화, 문서 로드 | 🔴 필수 |
| 5-3 | RAG 검색 파이프라인 | 상황 → 쿼리 → Top-K 문서 → 프롬프트 주입 | 🔴 필수 |
| 5-4 | MCP Tool 서버 구현 | Agent용 Tool 함수 정의 및 등록 | 🔴 필수 |
| 5-5 | Agent에 MCP 연동 | LangChain Tool 형태로 Agent에 바인딩 | 🔴 필수 |
| 5-6 | 슈퍼바이저 MCP 연동 | 슈퍼바이저 전용 Tool 추가 | 🟡 권장 |

---

### Phase 6: 풀 게임 통합 테스트 (3~4일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 6-1 | 단위 테스트 | 게임 엔진, 투표, 능력 로직 | 🔴 필수 |
| 6-2 | Agent 발언 품질 테스트 | 직업별 발언이 자연스러운지 검토 | 🔴 필수 |
| 6-3 | 전체 게임 시뮬레이션 | AI vs AI 전체 게임 자동 실행 | 🔴 필수 |
| 6-4 | 사람 참여 통합 테스트 | 실제 플레이어 참여 테스트 | 🔴 필수 |
| 6-5 | 승리 조건 엣지 케이스 | 광대 승리, 동률, 최소 인원 등 | 🟡 권장 |
| 6-6 | 성능 테스트 | 19개 Agent 동시 실행 응답 속도 | 🟡 권장 |

---

### Phase 7: UI 다듬기 + 배포 (2~3일)

| # | 작업 | 설명 | 우선순위 |
|---|------|------|----------|
| 7-1 | CSS 스타일링 | 낮/밤 테마, 색상 팔레트 적용 | 🟡 권장 |
| 7-2 | 타이머 애니메이션 | 프로그레스바 실시간 갱신 | 🟡 권장 |
| 7-3 | 에러 처리 | API 오류, 연결 끊김 대응 | 🔴 필수 |
| 7-4 | 환경 구성 문서 | README.md, 실행 방법 | 🔴 필수 |
| 7-5 | Docker 구성 | Dockerfile, docker-compose.yml | 🟢 선택 |

---

## 3. 프로젝트 디렉토리 구조 (제안)

```
ai-mafia/
├── docs/
│   └── planning/            ← 기획 문서 (현재 폴더)
│       ├── PRD.md
│       ├── GAME_RULES.md
│       ├── TECH_ARCHITECTURE.md
│       ├── AGENT_DESIGN.md
│       ├── UI_DESIGN.md
│       └── TASK_PLAN.md
│
├── backend/
│   ├── main.py              ← FastAPI 진입점
│   ├── websocket/
│   │   ├── manager.py       ← WebSocket 연결 관리
│   │   └── events.py        ← 이벤트 타입 정의
│   ├── game/
│   │   ├── engine.py        ← 게임 엔진 코어
│   │   ├── phase.py         ← Phase Manager
│   │   ├── timer.py         ← 타이머 시스템
│   │   ├── vote.py          ← 투표 시스템
│   │   ├── roles.py         ← 직업 정의 및 능력
│   │   └── win_condition.py ← 승리 조건 판정
│   ├── agents/
│   │   ├── graph.py         ← LangGraph Main Graph
│   │   ├── player_agent.py  ← 개별 Agent 노드
│   │   ├── persona.py       ← 페르소나 정의
│   │   └── pool.py          ← Agent Pool 관리
│   ├── supervisors/
│   │   ├── citizen.py       ← 시민 슈퍼바이저
│   │   ├── mafia.py         ← 마피아 슈퍼바이저
│   │   └── neutral.py       ← 중립 슈퍼바이저
│   ├── rag/
│   │   ├── knowledge/       ← 지식베이스 문서 (.txt, .md)
│   │   ├── store.py         ← ChromaDB 초기화
│   │   └── retriever.py     ← 검색 파이프라인
│   ├── mcp/
│   │   ├── tools.py         ← MCP Tool 정의
│   │   └── server.py        ← MCP 서버 설정
│   └── models/
│       ├── game.py          ← GameState, Player 모델
│       ├── chat.py          ← ChatMessage 모델
│       └── directive.py     ← Directive, Report 모델
│
├── frontend/
│   ├── app.py               ← Streamlit 메인
│   ├── pages/
│   │   ├── lobby.py         ← 로비 화면
│   │   ├── game.py          ← 게임 화면
│   │   └── result.py        ← 결과 화면
│   ├── components/
│   │   ├── chat_area.py     ← 채팅 영역
│   │   ├── status_panel.py  ← 상태창
│   │   └── player_card.py   ← 플레이어 카드
│   └── assets/
│       └── style.css        ← 커스텀 CSS
│
├── tests/
│   ├── test_game_engine.py
│   ├── test_agents.py
│   └── test_websocket.py
│
├── .env.example
├── requirements.txt
├── README.md
└── docker-compose.yml
```

---

## 4. 개발 우선순위 요약

```
1단계 (MVP 목표)
  → 게임 엔진 + 단순 AI Agent + WebSocket 채팅 동작
  → 낮/밤 사이클, 투표, 승리 판정 동작 확인

2단계 (AI 고도화)
  → 슈퍼바이저 + A2A 지시 체계
  → RAG로 전략적 발언 품질 향상

3단계 (완성도)
  → MCP Tool 연동
  → UI 스타일링 및 UX 개선
  → 에러 처리 및 배포 준비
```

---

## 5. Git 커밋 규칙 (제안)

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
chore: 설정, 의존성 변경
test: 테스트 추가
refactor: 리팩토링

예시:
feat: add phase manager with asyncio timer
feat: implement citizen supervisor with A2A directive
docs: add GAME_RULES with special event rules
fix: fix vote tie-breaking logic
```

---

## 6. 브랜치 전략

```
main          ← 안정 버전
dev           ← 개발 통합
feat/game-engine
feat/agent-system
feat/websocket
feat/rag-integration
feat/ui-streamlit
```
