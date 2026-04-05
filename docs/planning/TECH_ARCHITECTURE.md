# 기술 아키텍처 명세서 (TECH_ARCHITECTURE)

> **문서 버전**: v1.2  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-04-05  
> **변경 내용**: 투표/능력 통신 방식 WebSocket → REST 변경 기록, 구현 현황 반영

---

## 1. 시스템 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                       │
│              Streamlit (Browser UI)                  │
│   WebSocket (이벤트 수신)  +  HTTP REST (액션 전송)   │
└──────────────────┬───────────────────┬──────────────┘
                   │ WebSocket         │ HTTP POST
┌──────────────────▼───────────────────▼──────────────┐
│              FastAPI Main Server                     │
│                                                      │
│  ┌──────────────┐  ┌───────────────────────────┐    │
│  │ WebSocket    │  │ REST API                  │    │
│  │ Manager      │  │ POST /game/{id}/chat      │    │
│  │ (이벤트 Push)│  │ POST /game/{id}/vote      │    │
│  │              │  │ POST /game/{id}/ability   │    │
│  └──────┬───────┘  └───────────────────────────┘    │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │         Game Engine + GameRunner             │    │
│  │   Phase / Timer / Vote / Ability / Snapshot  │    │
│  └──────┬──────────────────────────────────────┘    │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │      LangGraph Orchestrator (AgentGraph)     │    │
│  │  StateGraph + Node/Edge + 슈퍼바이저 조율     │    │
│  └──────┬──────────────────────────────────────┘    │
│         │                                            │
│  ┌──────▼──────────────────────────────────────┐    │
│  │      AI Agent Pool (최대 19개)               │    │
│  │  Agent_1 ... Agent_N (LangGraph Node)        │    │
│  └──────┬──────────────────────────────────────┘    │
└─────────┼────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────┐
│              공유 저장소 레이어                       │
│  ┌─────────────────────┐  ┌────────────────────┐   │
│  │  Redis (필수)        │  │ ChromaDB (RAG)     │   │
│  │  - 게임 세션 상태    │  │ - 전략 지식베이스  │   │
│  │  - LangGraph         │  │ - 발언 패턴        │   │
│  │    Checkpointer      │  │ - 상황별 사례      │   │
│  │  - Supervisor        │  │ - 룰 문서          │   │
│  │    Directive         │  └────────────────────┘   │
│  └─────────────────────┘                            │
└─────────────────────────────────────────────────────┘
```

---

## 2. 서버 구성 전략

### 2.1 기본: 단일 FastAPI 서버
```
backend/
├── main.py              # FastAPI 앱 + REST API + WebSocket
├── websocket/           # WebSocket 연결 관리
├── game/                # engine, runner, registry, snapshot, vote, roles, phase, timer, win_condition
├── agents/              # LangGraph AgentGraph, PlayerAgent, AgentPool, persona
├── supervisors/         # citizen, mafia, neutral
├── rag/                 # store, retriever
├── mcp/                 # tools, server
└── models/              # game, chat, directive
```

---

## 3. 통신 설계

### 3.1 통신 방식 구분

> ⚠️ **설계 변경 기록 (2026-03-19)**  
> 초기 설계: 투표·능력 사용을 WebSocket 이벤트로 처리  
> **실제 구현**: 프론트엔드가 투표·능력을 **HTTP REST POST**로 구현  
> → 채팅은 WebSocket, 액션(투표·능력)은 REST로 혼용하는 방식으로 확정

| 통신 방향 | 방식 | 대상 |
|----------|------|------|
| 서버 → 클라이언트 | **WebSocket** | 이벤트 Push (채팅, 상태 변경, 사망 등) |
| 클라이언트 → 서버 (채팅) | **WebSocket** | chat_message |
| 클라이언트 → 서버 (투표) | **HTTP REST** | POST /game/{id}/vote |
| 클라이언트 → 서버 (능력) | **HTTP REST** | POST /game/{id}/ability |

### 3.2 REST API 스펙

```
POST /game/{game_id}/chat
  Body: { sender: str, content: str, channel: str = "global" }
  Response: { status: "ok" }

POST /game/{game_id}/vote
  Body: { voter: str, voted_for: str | None }
  Response: { status: "ok" }

POST /game/{game_id}/ability
  Body: { player_name: str, ability: str, target: str }
  Note: "protect" → 서버 내부에서 "heal"로 자동 매핑
  Response: { status: "ok" }

GET /health
  Response: { status: "ok", rag_status: "ok"|"unknown"|"error", llm_provider: "anthropic"|"azure"|"disabled"|"fallback" }
```

### 3.3 WebSocket 이벤트 (서버 → 클라이언트)

```json
{ "event": "chat_broadcast",    "payload": { "sender", "content", "channel", "timestamp", "is_ai" } }
{ "event": "phase_change",      "payload": { "phase", "round" } }
{ "event": "game_state_update", "payload": { "players", "phase", "round", "timer_seconds" } }
{ "event": "player_death",      "payload": { "player", "role"(한글), "cause" } }
{ "event": "vote_result",       "payload": { "target", "votes", "executed" } }
{ "event": "ability_result",    "payload": { "type", "success", "detail" } }
{ "event": "game_over",         "payload": { "winner", "reason", "players" } }
```

### 3.4 채팅 채널 분리

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
    phase: Phase          # Enum: day_chat, day_vote, final_speech, final_vote,
                          #       night_mafia, night_ability, night_result
    round: int
    timer_seconds: int
    players: List[Player]
    chat_history: List[ChatMessage]
    events: List[GameEvent]
    directives: List[Directive]   # 슈퍼바이저 → Agent 지시
    reports: List[Report]         # Agent → 슈퍼바이저 보고
    winner: Optional[str]         # "citizen" | "mafia" | "jester" | "spy"
```

### 4.2 플레이어 (Player)
```python
class Player(BaseModel):
    id: str
    name: str
    role: Role            # citizen, detective, doctor, fortune_teller,
                          # mafia, killer, jester, spy
    team: Team            # citizen, mafia, neutral
    is_alive: bool
    is_human: bool
    trust_score: float    # 0.0 ~ 1.0 (슈퍼바이저 전략 기반)
    ability_used: bool
```

### 4.3 채팅 메시지 (ChatMessage)
```python
class ChatMessage(BaseModel):
    id: str
    sender: str
    content: str
    channel: str          # "global" | "mafia_secret" | "system"
    timestamp: datetime
    is_ai: bool
```

---

## 5. 메모리 계층 구조 (3단계)

```
┌─────────────────────────────────────────────────────┐
│  L1. Agent 실행 컨텍스트 (In-Memory, 단일 호출)      │
│      game_state 스냅샷, 최근 채팅, directive, RAG 결과│
├─────────────────────────────────────────────────────┤
│  L2. 게임 세션 메모리 (Redis)                        │
│      LangGraph Checkpointer (thread_id 기반)         │
│      thread_id = f"{game_id}_{agent_id}"            │
├─────────────────────────────────────────────────────┤
│  L3. 전략 지식베이스 (ChromaDB, 영구)                │
│      전략 문서, 발언 패턴, 상황별 사례, 룰 문서      │
└─────────────────────────────────────────────────────┘
```

### Redis 키 설계
```
game:{game_id}:state              → 전체 게임 상태 JSON
game:{game_id}:chat:{round}       → 라운드별 채팅 히스토리
game:{game_id}:events             → 게임 이벤트 로그
game:{game_id}:directives         → 슈퍼바이저 → Agent 지시
game:{game_id}:prologue           → 게임 프롤로그 텍스트
game:{game_id}:players            → 플레이어 목록 JSON
agent:{game_id}:{agent_id}:memory → Agent 개인 관찰 메모리
mafia:game_archive:{game_id}      → 게임 결과 아카이브 JSON (TTL 30일)
mafia:game_analysis:processed     → 분석 완료 게임 ID Set
```

---

## 6. Phase 타이머

```
DAY_CHAT      → 180초 (3분)
DAY_VOTE      → 60초
FINAL_SPEECH  → 30초 (최후 변론)
FINAL_VOTE    → 30초 (찬반 투표)
NIGHT_MAFIA   → 90초 (마피아 협의)
NIGHT_ABILITY → 60초 (직업 능력)
NIGHT_RESULT  → 10초 (결과 공개 대기)
```

GameRunner.run() 내부 asyncio.sleep()으로 타이머 관리.  
프론트는 JS interval로 독립적으로 카운트다운 표시.

---

## 7. 기술 의존성

```
Python               >= 3.11
FastAPI              >= 0.110
uvicorn
websockets
streamlit            >= 1.32
langchain            >= 0.2
langgraph            >= 0.1
langchain-anthropic
chromadb
sentence-transformers
pydantic             >= 2.0
redis                ✅ 필수
langgraph-checkpoint-redis
```

> ⚠️ Redis는 필수입니다. docker-compose.yml에 Redis 서비스가 포함되어야 합니다.
