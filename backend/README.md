# Backend — AI Mafia Online

> **담당**: Cursor AI  
> **이 파일은 Cursor가 직접 관리합니다.** 내용 변경 시 `.cursorrules` 규칙을 준수할 것.

---

## 기술 스택

| 항목 | 버전/내용 |
|------|----------|
| Python | >= 3.11 |
| FastAPI | >= 0.110 |
| LangGraph | >= 0.1 |
| LangChain-Anthropic | 최신 |
| ChromaDB | >= 0.5 |
| Redis | 필수 (LangGraph Checkpointer) |
| pytest | >= 8.0 |

---

## 로컬 실행

```bash
# 프로젝트 루트에서

# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# ANTHROPIC_API_KEY, REDIS_URL 등 입력

# 3. Redis 먼저 실행 (docker-compose 사용)
docker-compose up redis

# 4. 백엔드 실행
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 5. API 문서 확인
# http://localhost:8000/docs
```

---

## 환경변수

```env
MAFIA_LLM_PROVIDER=anthropic   # anthropic | azure
ANTHROPIC_API_KEY=          # Anthropic 모드 시
ANTHROPIC_MODEL=claude-sonnet-4
# Azure OpenAI (MAFIA_LLM_PROVIDER=azure)
AOAI_ENDPOINT=
AOAI_API_KEY=
AOAI_API_VERSION=2024-02-01
AOAI_DEPLOY_GPT4O=          # 채팅 배포 이름
MAFIA_USE_LLM=1              # 0: LLM 비활성화
REDIS_URL=redis://localhost:6379
# 로컬 기본 0(메모리). docker-compose의 backend 서비스는 MAFIA_USE_REDIS_CHECKPOINTER=1 로 설정됨.
MAFIA_USE_REDIS_CHECKPOINTER=0
CHROMA_PERSIST_DIR=./backend/rag/chroma_db
RAG_KNOWLEDGE_DIR=./backend/rag/knowledge
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
PORT=8000
# GAP-03: AI 추론 미리보기 WS (`agent_thought`). 0 으로 끔.
MAFIA_BROADCAST_AGENT_THOUGHTS=1
# reasoning_preview 최대 길이(문자)
MAFIA_AGENT_THOUGHT_MAX_CHARS=600
# RAG 검색 건수 로그: 1이면 INFO 한 줄, 0이면 DEBUG만
MAFIA_RAG_LOG_HITS=1
# RAG: Chroma 메타데이터 $or 필터 (역할·팀·공용 category). 0이면 필터 끔
MAFIA_RAG_METADATA_FILTER=1
# RAG: MMR 다양화 (0 꺼짐, 1 켜짐). MAFIA_RAG_MMR_LAMBDA=0.5 권장
MAFIA_RAG_USE_MMR=0
# Structured 출력 self-consistency: 1이면 단일 호출, 2~5면 병렬 샘플 후 병합
MAFIA_SELF_CONSISTENCY_N=1
MAFIA_SELF_CONSISTENCY_TEMP=0.55
```

### LangSmith · 멀티 POD (선택)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LANGCHAIN_TRACING_V2` | `false` | `true`이면 LangSmith 트레이싱 활성화 (`main.py`에서 프로젝트 설정) |
| `LANGCHAIN_API_KEY` | — | LangSmith API 키 (`TRACING_V2=true`일 때) |
| `LANGCHAIN_PROJECT` | `mafia-game` | LangSmith 프로젝트 이름 |
| `MAFIA_POD_ID` | — | 멀티 POD 식별자. 미설정 시 `backend/pod.py`가 hostname 사용 |

---

## 테스트 실행

```bash
# 프로젝트 루트에서

# LLM 없이 빠른 테스트
MAFIA_USE_LLM=0 pytest backend/tests/ -v

# 전체 테스트
pytest backend/tests/ -v

# Phase 6-7: AI vs AI 헤드리스 스모크 (chromadb + sentence-transformers 설치 필요)
MAFIA_USE_LLM=0 pytest backend/tests/test_ai_vs_ai_simulation.py -v
```

---

## 디렉토리 구조

```
backend/
├── README.md              ← 이 파일 (Cursor 관리)
├── Dockerfile
├── main.py                ← FastAPI 앱 진입점
├── config.py              ← LLM Provider(Anthropic/Azure) 중앙 설정
├── agents/
│   ├── graph.py           ← LangGraph AgentGraph
│   ├── player_agent.py    ← 개별 AI Agent (LLM 연동)
│   ├── analysis_agent.py  ← GameInsightAgent (게임 종료 후 RAG 자기학습)
│   ├── persona.py
│   └── pool.py
├── game/
│   ├── engine.py          ← 게임 엔진
│   ├── runner.py          ← 게임 루프 + WS 브로드캐스트
│   ├── registry.py        ← 게임 세션 관리 (create + get)
│   ├── composition.py     ← 인원별 직업 구성 (GAME_RULES 표 기반)
│   ├── snapshot.py
│   ├── phase.py
│   ├── vote.py
│   ├── roles.py
│   └── win_condition.py
├── supervisors/
│   ├── citizen.py         ← 시민팀 슈퍼바이저
│   ├── mafia.py           ← 마피아 슈퍼바이저
│   └── neutral.py
├── rag/
│   ├── store.py           ← ChromaDB 래퍼
│   ├── retriever.py       ← 전략 검색
│   └── knowledge/         ← 지식베이스 문서
├── mcp/
│   └── tools.py           ← MCPGameTools
├── websocket/
│   ├── manager.py         ← 연결 관리 + 채널 필터링
│   └── events.py
├── models/
│   ├── game.py
│   ├── chat.py
│   └── directive.py
└── tests/
    ├── conftest.py
    ├── test_ai_vs_ai_simulation.py  # 헤드리스 게임 종료 스모크
    ├── test_game_engine.py
    ├── test_agents.py
    └── test_websocket.py
```

---

## API 엔드포인트

### WebSocket
```
ws://localhost:8000/ws/{game_id}
```

`game_id`에 해당하는 게임이 **먼저** `POST /game/create`로 등록되어 있어야 한다. 없으면 연결 후 code `4000`으로 종료된다.

### REST
```
GET  /health                  → { status, rag_status, llm_provider }
                                # rag_status: ok | error | unknown
                                # llm_provider: anthropic | azure | disabled | fallback
POST /game/create             { host_name, player_count }  →  { game_id, player_count }
POST /game/{game_id}/chat     { sender, content, channel }
POST /game/{game_id}/vote     { voter, voted_for }
POST /game/{game_id}/ability  { player_name, ability, target }
```

- `POST /game/create`: `player_count`는 4~20. 응답의 `game_id`로 이후 WS·REST 호출.
- 알 수 없는 `game_id`로 chat/vote/ability 호출 시 **404**.

> `ability: "protect"` → 서버 내부에서 `"heal"` 로 자동 매핑

---

## 채팅 채널

| 채널 | 수신 가능 |
|------|----------|
| `global` | 전체 플레이어 |
| `mafia_secret` | 마피아 팀만 |
| `spy_listen` | 마피아 + 스파이 |
| `system` | 전체 (읽기 전용) |

---

## Dockerfile

```bash
# 루트에서 빌드
docker build -f backend/Dockerfile -t mafia-backend .
```
