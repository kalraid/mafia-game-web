# 기술 아키텍처 명세서 (TECH_ARCHITECTURE)

> **문서 버전**: v1.1  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-18  
> **변경 내용**: Redis 필수로 변경 (선택→필수), 메모리 계층 구조 추가

---

## 1. 시스템 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                       │
│              Streamlit (Browser UI)                  │
│         WebSocket Client (ws://localhost)            │
└──────────────────────┬──────────────────────────────┘
                       │ WebSocket / HTTP
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Main Server                     │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ WebSocket    │  │ REST API     │                 │
│  │ Manager      │  │ (게임 설정,  │                 │
│  │              │  │  로비 등)    │                 │
│  └──────┬───────┘  └──────────────┘                 │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │         Game Engine (게임 진행 로직)          │    │
│  │   Phase Manager / Timer / Vote Manager       │    │
│  └──────┬──────────────────────────────────────┘    │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │      LangGraph Orchestrator                  │    │
│  │  (Agent 실행 및 슈퍼바이저 조율)              │    │
│  └──────┬──────────────────────────────────────┘    │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │      AI Agent Pool (최대 19개)               │    │
│  │  Agent_1 ... Agent_N (각각 LangGraph Node)   │    │
│  └──────┬──────────────────────────────────────┘    │
└─────────┼────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────┐
│              공유 저장소 레이어                       │
│                                                      │
│  ┌─────────────────────┐  ┌────────────────────┐   │
│  │  Redis (필수)        │  │ ChromaDB (RAG)     │   │
│  │  - 게임 세션 상태    │  │ - 전략 지식베이스  │   │
│  │  - 채팅 히스토리     │  │ - 발언 패턴        │   │
│  │  - Agent 메모리      │  │ - 상황별 사례      │   │
│  │  - LangGraph         │  │ - 룰 문서          │   │
│  │    Checkpointer      │  └────────────────────┘   │
│  │  - Supervisor        │                            │
│  │    Directive         │                            │
│  └─────────────────────┘                            │
└─────────────────────────────────────────────────────┘
```

---

## 2. 서버 구성 전략

### 2.1 기본: 단일 FastAPI 서버
```
fastapi_main/
├── main.py              # FastAPI 앱 진입점
├── websocket/           # WebSocket 연결 관리
├── game/                # 게임 엔진 (Phase, Timer, Vote)
├── agents/              # LangGraph Agent 풀
├── supervisors/         # 슈퍼바이저 Agent
├── rag/                 # RAG 지식베이스
├── mcp/                 # MCP Tool 정의
└── models/              # 데이터 모델 (Pydantic)
```

### 2.2 확장: 서비스 분리 (부하 고려 시)
```
[서버 A] FastAPI Main    → 게임 엔진 + WebSocket 관리
[서버 B] Agent Worker 1  → Agent 1~6 (시민 계열)
[서버 C] Agent Worker 2  → Agent 7~13 (마피아+중립)
[서버 D] RAG Server      → ChromaDB + 임베딩 서비스
```
> 초기 개발은 단일 서버로 시작하고 성능 테스트 후 분리 여부 결정.

---

## 3. WebSocket 통신 설계

### 3.1 이벤트 타입 정의

```json
// 클라이언트 → 서버
{ "event": "chat_message", "payload": { "content": "나는 시민이야!", "sender": "player" } }
{ "event": "vote", "payload": { "target": "AI_Player_3" } }
{ "event": "use_ability", "payload": { "target": "AI_Player_5", "ability": "investigate" } }

// 서버 → 클라이언트
{ "event": "chat_broadcast", "payload": { "sender": "AI_Player_2", "content": "...", "timestamp": "...", "is_ai": true } }
{ "event": "phase_change", "payload": { "phase": "night", "round": 2 } }
{ "event": "player_death", "payload": { "player": "AI_Player_7", "role": "mafia", "cause": "vote" } }
{ "event": "game_state_update", "payload": { "players": [...], "phase": "day", "timer": 120 } }
{ "event": "vote_result", "payload": { "target": "AI_Player_3", "votes": 4, "executed": true } }
{ "event": "game_over", "payload": { "winner": "citizen", "reason": "all_mafia_eliminated" } }
```

### 3.2 채팅 채널 분리

| 채널 | 접근 권한 | 사용 시점 |
|------|----------|----------|
| `global` | 전체 플레이어 | 낮 Phase |
| `mafia_secret` | 마피아 전용 | 밤 Phase |
| `spy_listen` | 스파이 읽기 전용 | 밤 Phase (마피아 채널 미러) |
| `system` | 게임 엔진 → 전체 | 이벤트 알림 |

---

## 4. 데이터 모델

### 4.1 게임 상태 (GameState)
```python
class GameState(BaseModel):
    game_id: str
    phase: Literal["day", "night", "vote", "ability"]
    round: int
    timer_seconds: int
    players: List[Player]
    chat_history: List[ChatMessage]
    events: List[GameEvent]
    directives: List[Directive]      # 슈퍼바이저 → Agent 지시
    reports: List[Report]            # Agent → 슈퍼바이저 보고
    winner: Optional[str]
```

### 4.2 플레이어 (Player)
```python
class Player(BaseModel):
    id: str
    name: str
    role: Role           # citizen, detective, doctor, fortune_teller,
                         # mafia, killer, jester, spy
    team: Team           # citizen, mafia, neutral
    is_alive: bool
    is_human: bool
    trust_score: float   # 0.0 ~ 1.0 (AI 내부 신뢰도)
    ability_used: bool
```

### 4.3 채팅 메시지 (ChatMessage)
```python
class ChatMessage(BaseModel):
    id: str
    sender: str
    content: str
    channel: str         # "global" | "mafia_secret" | "system"
    timestamp: datetime
    is_ai: bool
```

---

## 5. 메모리 계층 구조 (3단계)

```
┌─────────────────────────────────────────────────────┐
│  L1. Agent 실행 컨텍스트 (In-Memory, 단일 호출)      │
│      현재 호출에 필요한 정보만 로드                   │
│      game_state 스냅샷, 최근 채팅 10개, directive    │
├─────────────────────────────────────────────────────┤
│  L2. 게임 세션 메모리 (Redis, 게임 종료까지 유지)    │
│      전체 채팅 히스토리, 이벤트 로그, trust_score    │
│      LangGraph Checkpointer로 연동                   │
│      thread_id = f"{game_id}_{agent_id}"            │
├─────────────────────────────────────────────────────┤
│  L3. 전략 지식베이스 (ChromaDB, 영구 유지)           │
│      전략 문서, 발언 패턴, 상황별 사례, 룰 문서      │
│      게임 간 공유, 의미 기반 검색                    │
└─────────────────────────────────────────────────────┘
```

### Redis 키 설계
```
game:{game_id}:state              → 전체 게임 상태 JSON
game:{game_id}:prologue           → 게임 시작 설정 (인원, 직업 배분)
game:{game_id}:players            → 플레이어별 정보
game:{game_id}:chat:{round}       → 라운드별 채팅 히스토리
game:{game_id}:events             → 게임 이벤트 로그
game:{game_id}:directives         → 슈퍼바이저 → Agent 지시
agent:{game_id}:{agent_id}:memory → Agent 개인 관찰 메모리
```

---

## 6. Phase 타이머 관리

```
DAY_CHAT      → 180초 (3분)
DAY_VOTE      → 60초  (1분)
FINAL_SPEECH  → 30초  (최후 변론)
FINAL_VOTE    → 30초  (찬반 투표)
NIGHT_MAFIA   → 90초  (마피아 협의)
NIGHT_ABILITY → 60초  (직업 능력)
NIGHT_RESULT  → 10초  (결과 공개 대기)
```

각 Phase는 서버 측 asyncio 타이머로 관리.  
타이머 종료 시 자동으로 다음 Phase 전환 이벤트 발생.

---

## 7. 기술 의존성 정리

```
Python               >= 3.11
FastAPI              >= 0.110
uvicorn              (ASGI 서버)
websockets           (WebSocket 지원)
streamlit            >= 1.32
langchain            >= 0.2
langgraph            >= 0.1
langchain-anthropic
chromadb             (RAG 벡터 DB)
sentence-transformers (임베딩)
pydantic             >= 2.0
asyncio              (비동기 처리)
redis                ✅ 필수 (LangGraph Checkpointer + 세션 저장)
langgraph-checkpoint-redis  (LangGraph Redis 연동)
```

> ⚠️ **Redis는 필수**입니다. 단일 서버 구성에서도 LangGraph Checkpointer와
> Agent 멀티턴 메모리를 위해 반드시 실행되어야 합니다.
> `docker-compose.yml`에 Redis 서비스를 포함해야 합니다.
