# 🎭 AI Mafia Online

> AI 플레이어와 함께 즐기는 웹 마피아 게임.  
> 최대 20인, LangGraph 기반 AI Agent, RAG 전략 학습, 실시간 WebSocket 통신.

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **Frontend** | Streamlit (포트 8501) |
| **Backend** | FastAPI + LangGraph + LangChain (포트 8000) |
| **AI** | Claude API (anthropic) 또는 Azure OpenAI — `MAFIA_LLM_PROVIDER`로 전환, 없으면 Fallback 모드 |
| **DB** | ChromaDB (RAG 벡터 DB) |
| **세션** | Redis + LangGraph Checkpointer |
| **통신** | WebSocket (이벤트 Push) + HTTP REST (액션) |

---

## 빠른 시작 (docker-compose)

```bash
# 1. 환경변수 준비
cp .env.example .env
# .env 편집: ANTHROPIC_API_KEY 입력 (없으면 Fallback 모드로 동작)

# 2. 빌드 및 실행
docker-compose up --build

# 3. 접속
# 프론트엔드:  http://localhost:8501
# 백엔드 API:  http://localhost:8000/docs
# Redis:      localhost:6379
```

> **ANTHROPIC_API_KEY 없이도 실행 가능합니다.**  
> AI 발언·투표·능력이 랜덤 Fallback 으로 동작합니다.

---

## 로컬 개발 (개별 실행)

### 사전 준비

```bash
cp .env.example .env
# ANTHROPIC_API_KEY, REDIS_URL 등 설정
```

### Redis 실행

```bash
docker-compose up redis
```

### Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

자세한 내용 → [`backend/README.md`](backend/README.md)

### Frontend

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

자세한 내용 → [`frontend/README.md`](frontend/README.md)

---

## 게임 방법

1. `http://localhost:8501` 접속
2. 닉네임 입력 + 인원 수 설정 후 **게임 시작**
3. 낮에는 채팅으로 마피아를 찾아 투표 처형
4. 밤에는 각 직업 능력 사용 (마피아 공격 / 경찰 조사 / 의사 보호 등)
5. 시민 팀 또는 마피아가 승리 조건 달성 시 종료

### 직업 구성 (8인 기준)

| 직업 | 팀 | 능력 |
|------|-----|------|
| 시민 | 시민 | 없음 |
| 경찰 | 시민 | 밤: 1명 조사 |
| 의사 | 시민 | 밤: 1명 보호 |
| 마피아 | 마피아 | 밤: 1명 공격 |

---

## 프로젝트 구조

```
mafia-game-web/
├── CLAUDE.md              ← Claude AI 컨텍스트 파일
├── .cursorrules           ← Cursor AI 자동 규칙
├── .geminirules           ← Gemini AI 참조 규칙
├── docker-compose.yml     ← 전체 서비스 구성 (Claude 관리)
├── .env.example           ← 환경변수 템플릿
├── requirements.txt       ← 백엔드 Python 의존성
│
├── backend/               ← FastAPI 서버 (Cursor 담당)
│   ├── README.md
│   ├── Dockerfile
│   ├── main.py
│   ├── agents/            ← LangGraph Agent
│   ├── game/              ← 게임 엔진
│   ├── supervisors/       ← AI 슈퍼바이저
│   ├── rag/               ← ChromaDB + 지식베이스
│   ├── mcp/               ← MCP Tools
│   ├── websocket/         ← WebSocket 관리
│   ├── models/            ← Pydantic 모델
│   └── tests/
│
└── frontend/              ← Streamlit UI (Gemini 담당)
    ├── README.md
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    ├── pages/
    ├── components/
    ├── assets/
    └── tests/
```

---

## 환경변수 (.env)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `MAFIA_LLM_PROVIDER` | `anthropic` | LLM Provider 선택: `anthropic` \| `azure` |
| `ANTHROPIC_API_KEY` | — | Claude API 키 (없으면 Fallback) |
| `ANTHROPIC_MODEL` | `claude-sonnet-4` | 사용할 Claude 모델 |
| `MAFIA_USE_LLM` | `1` | `0` 설정 시 LLM 전체 비활성화 (Fallback 모드) |
| `REDIS_URL` | `redis://localhost:6379` | Redis 연결 주소 (docker-compose에서는 `redis://redis:6379` 자동 적용) |
| `MAFIA_USE_REDIS_CHECKPOINTER` | `0` (로컬) | `1` 설정 시 LangGraph Redis 체크포인터 활성화 — docker-compose에서 자동으로 `1` |
| `PORT` | `8000` | 백엔드 포트 |
| `CHROMA_PERSIST_DIR` | `./backend/rag/chroma_db` | ChromaDB 저장 경로 |
| `LANGCHAIN_TRACING_V2` | `false` | `true` 설정 시 LangSmith 트레이싱 활성화 (선택) |
| `LANGCHAIN_API_KEY` | — | LangSmith API 키 (`LANGCHAIN_TRACING_V2=true` 시) |
| `MAFIA_POD_ID` | — | 멀티POD 환경 식별자 — 미설정 시 hostname 자동 사용 (선택) |

---

## LLM Provider 선택

`MAFIA_LLM_PROVIDER` 환경변수 하나로 LLM 제공자를 전환합니다.

| 모드 | 환경변수 설정 | 설명 |
|------|------------|------|
| **Anthropic Claude** (기본) | `MAFIA_LLM_PROVIDER=anthropic` | `ANTHROPIC_API_KEY` 필요 |
| **Azure OpenAI** | `MAFIA_LLM_PROVIDER=azure` | `AOAI_ENDPOINT`, `AOAI_API_KEY`, `AOAI_DEPLOY_GPT4O` 필요 |
| **Fallback** (LLM 없음) | `MAFIA_USE_LLM=0` | AI가 랜덤 행동으로 동작, API 키 불필요 |

Azure OpenAI 상세 환경변수는 `.env.example` 참조.

---

## 팀 구성

| 역할 | 담당 | AI 파일 |
|------|------|--------|
| 기획 + 인프라 | Claude | `CLAUDE.md` |
| 백엔드 개발 | Cursor | `.cursorrules` |
| 프론트엔드 개발 | Gemini | `.geminirules` |

---

## 관련 문서

- [기술 아키텍처](docs/planning/TECH_ARCHITECTURE.md)
- [게임 룰](docs/planning/GAME_RULES.md)
- [AI Agent 설계](docs/planning/AGENT_DESIGN.md)
- [작업 계획](docs/planning/TASK_PLAN.md)

2026-04-06
