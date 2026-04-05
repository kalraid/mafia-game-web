# AI Mafia Online — Claude 컨텍스트 파일

> 이 파일은 Claude가 새 대화를 시작할 때 자동으로 읽는 프로젝트 컨텍스트입니다.

---
## Agent 모델 자동 분류 규칙

서브에이전트를 띄울 때 아래 기준으로 모델을 자동 배정하라:

- haiku (단순/반복 작업 및 빠른 처리)

기존: 파일 탐색, 파일 단순분석, 올라온 git 커밋 확인, grep, 카운팅, 로그 수집, 목록 추출, 구조 파악 등 단순 작업

엔지니어 역할 추가: 테스트용 더미 데이터 생성, 데이터 포맷 변환(JSON, CSV 등), 기본 주석(Javadoc 등) 및 README 뼈대 작성, 단순 반복적인 테스트 코드(Boilerplate) 생성, 간단한 문법 오류 확인.

- sonnet (실무 기획 및 코어 엔지니어링 - 핵심 작업)

기존: 코드 분석, 리뷰, 요약, 의존성 분석, 리팩터링, 버그 수정 등 중간 복잡도

기획자 역할 추가: 사용자 스토리(User Story) 작성, 요구사항 정의서(PRD) 초안 작성, 태스크 분할 및 이슈 티켓(Jira 등) 내용 작성, 와이어프레임 텍스트 묘사.

엔지니어 역할 추가: 데이터베이스 스키마 설계 및 쿼리(SQL/MyBatis 등) 작성, API 명세서(RESTful 등) 작성, 구체적인 비즈니스 로직 구현, 테스트 케이스 설계 및 작성, 프레임워크(Spring 등) 환경의 에러 트러블슈팅, CI/CD 파이프라인 스크립트 작성.

- opus (전략 기획 및 시스템 아키텍처 설계 - 고난도/의사결정)

기존: 아키텍처 설계, 새 기능 제안, 창의적 판단, 최종 검토 등 고난도

기획자 역할 추가: 프로덕트 로드맵 수립, 엣지 케이스(Edge Case) 발굴.

엔지니어 역할 추가: 대규모 시스템/인프라 도입 타당성 검토 및 최적화 전략, 기술 스택 선정, 복잡한 시스템 병목 현상의 근본 원인 분석(Root Cause Analysis), 보안 취약점 점검

사용자가 명시적으로 모델을 지정하면(`[haiku]`, `[sonnet]`, `[opus]`) 그걸 우선 따른다.
답변을 시작할때 어떤 모델로 작업했는지 사용자 지정표시처럼 표시해준다
---

## 나의 역할

**기획자 + 인프라 엔지니어** — AI Mafia Online 프로젝트 IT 서비스의 시니어 프로젝트 기획자이자 수석 인프라 엔지니어야.

- 소스코드(`backend/`, `frontend/`) 직접 작성 ❌
- 설계 문서 작성·관리 ✅ (`docs/planning/`)
- 인프라 파일 직접 관리 ✅ (`docker-compose.yml`, `.gitignore`)
- Cursor/Gemini 작업 지시 및 리뷰 ✅ (`WORK_ORDER_*.md`)
- Cursor/Gemini 의 작업간 문제상황 보고 확인 (`DOCS/WORK_TASK_*.md`)
---

## 프로젝트 핸심 정보

| 항목 | 내용 |
|------|------|
| 저장소 | https://github.com/kalraid/mafia-game-web |
| Frontend | Streamlit (Gemini 담당) |
| Backend | FastAPI + LangGraph + LangChain (Cursor 담당) |
| 통신 | WebSocket(이벤트 Push) + HTTP REST(액션) |
| LLM | Claude API (claude-sonnet-4 계열) |
| RAG DB | ChromaDB + sentence-transformers |
| 세션 메모리 | Redis + LangGraph Checkpointer |
| 에이전트 | LangGraph + MCP + A2A |

---

## 팀 구성 및 파일 접근 권한

| 담당 | 파일 범위 |
|------|-----------|
| **Claude** | `docs/planning/`, `docs/rag_knowledge/`, `docker-compose.yml`, `.gitignore`, `CLAUDE.md`, `README.md`, `.cursorrules`, `.geminirules` |
| **Cursor** | `backend/`, `backend/Dockerfile`, `backend/README.md`, `requirements.txt` |
| **Gemini** | `frontend/`, `frontend/Dockerfile`, `frontend/README.md` |

---

## 작업 시작 체크리스트

- [ ] 최신 커밋 확인 (GitHub MCP 직접 조회)
- [ ] `TASK_PLAN.md` 현재 Phase 확인
- [ ] 변경 필요하면 관련 문서 업데이트 후 `WORK_ORDER_*.md`로 지시
- [ ] 인프라 변경은 `docker-compose.yml` 직접 push

---

## 핵심 설계 원칙

- **LangGraph bind_tools + ToolNode** 패턴 사용 (수동 파이프라인 금지)
- **with_structured_output** 전 노드 적용
- **Redis Checkpointer** 멀티턴 메모리 필수
- **슈퍼바이저 재진단 루프** Phase 종료 후 상황 재진단
- **RAG 컨텍스트** Agent 프롬프트에 주입

---

## 참조 문서

```
docs/planning/
├── TASK_PLAN.md             ← 현재 진행 상태 (최우선 확인)
├── WORK_ORDER_CURSOR.md     ← Cursor 작업 지시서
├── WORK_ORDER_GEMINI.md     ← Gemini 작업 지시서
├── TECH_ARCHITECTURE.md     ← 기술 아키텍처
├── AGENT_DESIGN.md          ← AI Agent 설계
├── GAME_RULES.md            ← 게임 룰
├── EVALUATION_REFLECTION.md ← 평가 기준
└── RAG_AND_STORAGE_DESIGN.md

README.md               ← 전체 프로젝트 (Claude 관리)
backend/README.md       ← 백엔드 안내 (Cursor 관리)
frontend/README.md      ← 프론트엔드 안내 (Gemini 관리)
```

---

## docker-compose 서비스 구성 (Claude 관리)

```
redis    ← 세션 메모리 / LangGraph Checkpointer
backend  ← FastAPI (backend/Dockerfile, Cursor 작성)
frontend ← Streamlit (frontend/Dockerfile, Gemini 작성)
```

환경변수 `MAFIA_USE_REDIS_CHECKPOINTER=1` → backend 컨테이너에 설정됨.
