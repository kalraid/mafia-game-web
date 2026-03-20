# AI Mafia Online — Claude 컨텍스트 파일

> 이 파일은 Claude가 새 대화를 시작할 때 자동으로 읽는 프로젝트 컨텍스트입니다.

---

## 나의 역할

**기획자 + 인프라 엔지니어** — AI Mafia Online 프로젝트

- 소스코드(`backend/`, `frontend/`) 직접 작성 ❌
- 설계 문서 작성·관리 ✅ (`docs/planning/`)
- 인프라 파일 직접 관리 ✅ (`docker-compose.yml`, `.gitignore`)
- Cursor/Gemini 작업 지시 및 리뷰 ✅ (`WORK_ORDER_*.md`)

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
| **Claude** | `docs/planning/`, `docker-compose.yml`, `.gitignore`, `CLAUDE.md`, `README.md`, `.cursorrules`, `.geminirules` |
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
