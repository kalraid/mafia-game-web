# 작업 계획서 (TASK_PLAN)

> **문서 버전**: v1.8  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-19  
> **기준 커밋**: `82e0600` (프론트엔드 작업본 260319-1)

---

## 1. 개발 단계 개요 및 현재 상태

```
Phase 0: 환경 구성 & 기반 작업        ✅ 완료
Phase 1: 게임 엔진 코어               ✅ 완료
Phase 2: AI Agent 기초                ✅ 완료 (LLM 연동, RAG 연결, Fallback)
Phase 3: WebSocket + 채팅 UI          ✅ 완료 (REST API 혼용, 결과화면 완성)
Phase 4: 슈퍼바이저 + A2A 연동        🔄 부분 완료 (전략 로직 구현, bind_tools/Redis 미완)
Phase 5: RAG + MCP 통합               🔄 부분 완료 (RAG Agent 연결 완료, 지식베이스 최소)
Phase 6: 풀 게임 통합 테스트          🔄 테스트 파일 작성 (실행 여부 미확인)
Phase 7: UI 다듬기 + 배포             ✅ 대부분 완료 (Dockerfile 양쪽, CSS, 결과화면 완성)
```

---

## 2. 작업 항목 상세

### Phase 0: 환경 구성 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 0-1 | 프로젝트 구조 생성 | ✅ 완료 | |
| 0-2 | 의존성 정의 | ✅ 완료 | 루트 `requirements.txt` + `frontend/requirements.txt` 분리 |
| 0-3 | Git 저장소 초기화 | ✅ 완료 | |
| 0-4 | 환경변수 설계 | ✅ 완료 | `.env.example` |
| 0-5 | Docker 구성 | ✅ 완료 | backend + frontend + redis 3서비스 |
| 0-6 | `.gitignore` 추가 | ✅ 완료 | `__pycache__`, `.env`, `chroma_db` 등 제외 |

---

### Phase 1: 게임 엔진 코어 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 1-1 | 데이터 모델 정의 | ✅ 완료 | `models/game.py` |
| 1-2 | Phase Manager | ✅ 완료 | |
| 1-3 | 타이머 시스템 | ✅ 완료 | `GameRunner.run()` asyncio 루프 |
| 1-4 | 직업 배분 로직 | ✅ 완료 | |
| 1-5 | 투표 시스템 | ✅ 완료 | |
| 1-6 | 직업 능력 처리 | ✅ 완료 | `engine.submit_ability()` |
| 1-7 | 승리 조건 판정 | ✅ 완료 | |
| 1-8 ~ 1-11 | GameRunner, Snapshot 등 | ✅ 완료 | |
| 1-12 | 게임 로그 | 🔄 부분 | `player_death` 이벤트만 로깅 |

---

### Phase 2: AI Agent 기초 ✅ 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 2-1 | LangChain + Claude API 연동 | ✅ 완료 | |
| 2-2 | Structured Output 스키마 | ✅ 완료 | `AgentDecision` |
| 2-3 | Phase별 행동 분기 + 가드 | ✅ 완료 | DAY_CHAT / DAY_VOTE / NIGHT_MAFIA / NIGHT_ABILITY |
| 2-4 | Fallback 처리 | ✅ 완료 | CI/MAFIA_USE_LLM=0 지원 |
| 2-5 | RAG → Agent 프롬프트 주입 | ✅ 완료 | `StrategyRetriever` lazy singleton |
| 2-6 | 발언 타이밍 딜레이 | ✅ 완료 | `_speech_delay()` verbosity 기반 |
| 2-7 | Agent 페르소나 시스템 | 🔄 확인 필요 | `persona.py` 내용 미확인 |
| 2-8 | Agent Pool 관리 | 🔄 확인 필요 | `pool.py` 내용 미확인 |
| 2-9 | Redis Checkpointer | ⬜ 미구현 | thread_id config만 존재 |

---

### Phase 3: WebSocket + 채팅 UI ✅ 완료 (REST 혼용)

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 3-1 ~ 3-6 | FastAPI WebSocket + REST API | ✅ 완료 | |
| 3-7 | Streamlit 메인 레이아웃 | ✅ 완료 | WS_URL 환경변수 지원 추가 |
| 3-8 | 채팅 영역 | ✅ 완료 | 마피아 채널 탭 분리, phase 입력 제한 |
| 3-9 | 상태창 | ✅ 완료 | |
| 3-10 | 플레이어 카드 | ✅ 완료 | CSS 기반 dead-overlay |
| 3-11 | 로비 화면 | ✅ 완료 | |
| 3-12 | 게임 화면 | 🔄 확인 필요 | `pages/game.py` 내용 미확인 |
| 3-13 | 결과 화면 | ✅ 완료 | winner 표시, 직업 공개, 버튼 |
| 3-14 | WebSocket 이벤트 핸들러 | ✅ 완료 | |

---

### Phase 4: 슈퍼바이저 + A2A 연동 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 4-1 | LangGraph StateGraph 도입 | ✅ 완료 | |
| 4-2 | 슈퍼바이저 → Agent 지시 흐름 | ✅ 완료 | |
| 4-3 | 시민 슈퍼바이저 전략 | ✅ 구현 | trust_score + reports 기반 |
| 4-4 | 마피아 슈퍼바이저 전략 | ✅ 구현 | detective > doctor > trust_score 우선순위 |
| 4-5 | 중립 슈퍼바이저 | 🔄 확인 필요 | |
| 4-6 | NIGHT_MAFIA 라운드 | ✅ 완료 | mafia_secret 채널 발언 |
| 4-7 | A2A Directive 시스템 | ✅ 완료 | |
| 4-8 | 슈퍼바이저 재진단 루프 | ⬜ 미구현 | |
| 4-9 | Redis Checkpointer | ⬜ 미구현 | |
| 4-10 | 마피아 채널 WS 필터링 | 🔄 부분 | mafia_secret 채널 전송 but 브로드캐스트 미필터링 |
| 4-11 | MCP bind_tools 패턴 | ⬜ 미구현 | MCPGameTools 직접 호출 중 |

---

### Phase 5: RAG + MCP 통합 🔄 부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 5-1 | ChromaDB RAGStore 구현 | ✅ 완료 | |
| 5-2 | 디스크 기반 문서 인덱싱 | ✅ 완료 | |
| 5-3 | StrategyRetriever 구현 | ✅ 완료 | |
| 5-4 | RAG → Agent 프롬프트 주입 | ✅ 완료 | |
| 5-5 | RAG 지식베이스 문서 | 🔄 최소 수준 | 6개 파일 (평가 기준 미달) |
| 5-6 | MCP Tool 구현 | ✅ 완료 | `MCPGameTools` |
| 5-7 | MCP → Agent bind_tools | ⬜ 미구현 | |
| 5-8 | 슈퍼바이저 MCP 연동 | ⬜ 미구현 | |

---

### Phase 6: 풀 게임 통합 테스트 🔄 파일 작성

> **테스트 구조**: 루트 `tests/` 폴더 없음. `backend/tests/` + `frontend/tests/` 각각 보유.

| # | 작업 | 상태 | 위치 |
|---|------|------|------|
| 6-1 | 게임 엔진 단위 테스트 | 🔄 작성 | `backend/tests/test_game_engine.py` |
| 6-2 | Agent 테스트 | 🔄 작성 | `backend/tests/test_agents.py` |
| 6-3 | WebSocket 테스트 | 🔄 작성 | `backend/tests/test_websocket.py` |
| 6-4 | 백엔드 pytest 설정 | ✅ 완료 | `backend/tests/conftest.py` |
| 6-5 | 프론트 E2E 테스트 | 🔄 작성 | `frontend/tests/e2e/test_lobby.py` |
| 6-6 | 프론트 유틸 단위 테스트 | 🔄 작성 | `frontend/tests/pytest/test_utils.py` |
| 6-7 | 전체 게임 시뮬레이션 | ⬜ 미작성 | AI vs AI 자동 실행 |

---

### Phase 7: UI 다듬기 + 배포 ✅ 대부분 완료

| # | 작업 | 상태 | 비고 |
|---|------|------|------|
| 7-1 | Docker 구성 (backend) | ✅ 완료 | |
| 7-2 | Docker 구성 (frontend) | ✅ 완료 | `frontend/Dockerfile` 완성, compose 통합 |
| 7-3 | Docker 구성 (redis) | ✅ 완료 | docker-compose 관리 (Claude) |
| 7-4 | CSS 스타일링 | ✅ 완료 | 낮/밤 테마, 채팅 스타일, 사망 오버레이 |
| 7-5 | 타이머 JS 애니메이션 | ✅ 완료 | `status_panel.py` 내 JS interval |
| 7-6 | 에러 처리 유틸 | 🔄 부분 | `handle_request_error()` 추가 |
| 7-7 | 결과 화면 완성 | ✅ 완료 | 직업 공개, 승패 표시, 버튼 |
| 7-8 | 루트 README.md | ✅ 완료 | |

---

## 3. 현재 이슈 목록 🚨

### 🔴 기획 불일치

| # | 이슈 | 상태 | 조치 |
|---|------|------|------|
| I-1 | 투표/능력 WebSocket → REST 변경 | ✅ 문서 반영 완료 | |
| I-2 | RAG → Agent 프롬프트 미연결 | ✅ 해결 | af1a977 |
| I-3 | MCP bind_tools 미적용 | ❌ 미해결 | Cursor: C-2 작업 |
| I-4 | 슈퍼바이저 전략 로직 미구현 | ✅ 해결 | af1a977 |
| I-5 | RAG 지식베이스 최소 수준 | ❌ 미해결 | Claude: 문서 추가 필요 |

### 🟡 중간 이슈

| # | 이슈 | 상태 | 조치 |
|---|------|------|------|
| I-6 | Redis Checkpointer 미연동 | ❌ 미해결 | Cursor: C-5 |
| I-7 | 발언 타이밍 딜레이 | ✅ 해결 | af1a977 |
| I-8 | 마피아 채널 WS 브로드캐스트 미필터링 | ❌ 미해결 | Cursor: C-4 |
| I-9 | `is-suspected-N` CSS 클래스 미정의 | 🟡 마이너 | Gemini: style.css에 추가 또는 player_card에서 제거 |

---

## 4. 프로젝트 디렉토리 현황 (2026-03-19 기준)

```
mafia-game-web/
├── .env.example                    ✅
├── .gitignore                      ✅
├── .nvmrc                          ✅
├── Dockerfile                      ✅ (backend, Cursor 담당)
├── docker-compose.yml              ✅ (Claude 관리 — backend+frontend+redis 3서비스)
├── requirements.txt                ✅ (backend 의존성)
├── README.md                       ✅
├── ROLE_CLAUDE.md / CURSOR.md / GEMINI.md  ✅
│
├── docs/planning/                  ✅ 문서 완비
│
├── backend/                        ✅ 대부분 완료
│   └── tests/                      🔄 파일 작성
│
└── frontend/
    ├── Dockerfile                  ✅ (Gemini 담당, compose 통합 완료)
    ├── requirements.txt            ✅ (프론트 전용 의존성)
    ├── app.py                      ✅ (WS_URL 환경변수 지원)
    ├── pages/
    │   ├── lobby.py                ✅
    │   ├── game.py                 🔄 확인 필요
    │   └── result.py               ✅ (winner/직업공개/버튼)
    ├── components/
    │   ├── chat_area.py            ✅
    │   ├── status_panel.py         ✅
    │   └── player_card.py          ✅ (dead-overlay CSS 기반)
    ├── assets/style.css            ✅ (낮/밤 테마 완성)
    └── tests/                      🔄 파일 작성
```

---

## 5. 최신 커밋 변경 요약

```
커밋 82e0600 — 프론트엔드 작업본 260319-1
  ✅ frontend/Dockerfile: 신규 (G-8 완료) → docker-compose frontend 서비스 활성화
  ✅ frontend/requirements.txt: 신규 (프론트 전용 의존성 분리)
  ✅ pages/result.py: G-5 완료 — winner/이유/직업공개/사망정보/버튼
  ✅ assets/style.css: G-6 완료 — 낮/밤 테마, 채팅 스타일, dead-overlay, 플레이어 카드
  ✅ app.py: WS_URL 환경변수로 변경 (컨테이너화 대응)
  🔄 player_card.py: is-suspected-N 클래스 사용 중이나 style.css에 미정의 (마이너)
  🔄 G-1 (voter 필드 확인) 명시적 완료 커밋 없음
```

---

## 6. 다음 우선 작업

### Claude 담당
```
1. RAG 지식 문서 추가 작성 (I-5)
   → backend/rag/knowledge/ 에 전략·발언패턴·상황 문서 20개+ 필요
```

### Cursor 담당
```
WORK_ORDER_CURSOR.md 참조
우선순위: C-2 (bind_tools) → C-4 (WS 채널 필터링) → C-5 (Redis) → C-7 (roles.py)
완료: C-1 ✅, C-3 ✅, C-6 ✅
```

### Gemini 담당
```
WORK_ORDER_GEMINI.md 참조
우선순위: G-1 (voter 필드 확인) → G-7 (game.py 레이아웃) → I-9 (is-suspected CSS)
완료: G-2 ✅, G-3 ✅, G-4 ✅, G-5 ✅, G-6 ✅, G-8 ✅
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
