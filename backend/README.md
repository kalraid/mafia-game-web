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
ANTHROPIC_API_KEY=          # LLM API 키 (없으면 Fallback 모드)
ANTHROPIC_MODEL=claude-sonnet-4
MAFIA_USE_LLM=1              # 0: LLM 비활성화
REDIS_URL=redis://localhost:6379
MAFIA_USE_REDIS_CHECKPOINTER=0  # 1: Redis Checkpointer 활성화
CHROMA_PERSIST_DIR=./backend/rag/chroma_db
RAG_KNOWLEDGE_DIR=./backend/rag/knowledge
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
PORT=8000
```

---

## 테스트 실행

```bash
# 프로젝트 루트에서

# LLM 없이 빠른 테스트
MAFIA_USE_LLM=0 pytest backend/tests/ -v

# 전체 테스트
pytest backend/tests/ -v
```

---

## 디렉토리 구조

```
backend/
├── README.md              ← 이 파일 (Cursor 관리)
├── Dockerfile
├── main.py                ← FastAPI 앱 진입점
├── agents/
│   ├── graph.py           ← LangGraph AgentGraph
│   ├── player_agent.py    ← 개별 AI Agent (LLM 연동)
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
GET  /health
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
