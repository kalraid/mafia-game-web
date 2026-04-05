# ⚙️ Cursor 작업 지시서 (WORK_ORDER_CURSOR)

> **대상**: Cursor AI — 백엔드 개발자
> **작성자**: Claude AI (기획자 + 인프라)
> **최종 업데이트**: 2026-04-05 (C-5 완료 반영 — 잔존 작업 없음)

> 작업 전 반드시 `ROLE_CURSOR.md`와 이 문서를 먼저 읽을 것.  
> **docker-compose.yml은 수정하지 않는다** — Claude 담당.

---

## 역할 구분

| 항목 | 담당 | 비고 |
|------|------|------|
| `backend/` 소스코드 | ✅ Cursor | |
| `backend/Dockerfile` | ✅ Cursor | 로컬 개발 및 빌드용 |
| `requirements.txt` | ✅ Cursor | |
| `docker-compose.yml` | ❌ Claude | **수정 금지** |

---

## ✅ 완료된 작업

| 항목 | 내용 | 커밋 |
|------|------|------|
| C-1 | RAG → player_agent 프롬프트 연결 | `af1a977` |
| C-3 | 슈퍼바이저 전략 로직 (trust_score + 우선순위) | `af1a977` |
| C-4 | 마피아 밤 채널 WebSocket 필터링 | `b6d9fe1` |
| C-6 | 발언 타이밍 딜레이 (`_speech_delay()`) | `af1a977` |
| C-2 | bind_tools + ToolNode ReAct 루프 완성 | `91150e0` |
| C-7 | `game/roles.py` 능력 로직 (detective/doctor/mafia/killer) | `3af6d3c` |
| C-8 | 슈퍼바이저 재진단 루프 (`supervisor_replan`) | `96becae` |
| C-9 | `docs/rag_knowledge` ChromaDB 인덱싱 (frontmatter 파싱) | `c77e002` |
| C-11-1 | `snapshot.py` FINAL_VOTE phase 문자열 수정 | `5f45e53` |
| C-11-2 | `mcp/tools.py` submit_vote 파라미터 통일 | `345831e` |
| C-11-3 | `roles.py` FORTUNE_TELLER/SPY handler 추가 | `1a79641` |
| C-10-1 | `game/archiver.py` GameArchiver Redis archive | `e531163` |
| C-10-2 | `agents/analysis_agent.py` GameInsightAgent LangGraph | `61a4ff4` |
| C-10-3 | `game/runner.py` 게임 종료 hook 추가 | `7f080d4` |
| C-10-4 | `rag/store.py` source="runtime" 메타데이터 충돌 방지 | `387ea8a` |
| C-10 | analyze_pending SCAN 배치 | `d691e80` |
| I-8 | `POST /game/create` + `composition.py` 인원별 직업 구성 + Registry get/create 분리 | `1baa68f` |
| C-5 | Redis Checkpointer 폴백 제거 — 실패 시 raise (폴백 없음) | `5b557a0` |

---

## ~~🔴 긴급 버그 수정~~ ✅ 완료

### ~~[C-11]~~ ✅ 완료 — 버그 3건 모두 수정 (`5f45e53`, `345831e`, `1a79641`)

---

#### ~~C-11-1~~: `backend/game/snapshot.py` — FINAL_VOTE phase 문자열 오류

**증상**: 프론트엔드가 FINAL_VOTE 단계에서 잘못된 phase값을 받아 UI 라우팅 오류.

**수정 내용**: `ui_phase()` 함수 내 `Phase.FINAL_VOTE` 매핑을 `"final_speech"` → `"final_vote"` 로 수정.

```python
# 현재 (❌)
Phase.FINAL_VOTE: "final_speech",

# 수정 (✅)
Phase.FINAL_VOTE: "final_vote",
```

---

#### C-11-2: `backend/mcp/tools.py` — `submit_vote()` 파라미터 불일치

**증상**: `player_agent.py`에서 `voter_id=self.player.id` 키워드로 호출하는데 `tools.py` 시그니처는 `agent_id`를 사용 → `TypeError` 발생 가능.

**수정 내용**: 둘 중 하나를 통일. `tools.py` 기준으로 맞춘다.

```python
# tools.py 현재 (예시)
def submit_vote(self, agent_id: str, target_id: str) -> bool: ...

# player_agent.py 현재 (❌ 불일치)
mcp_tools.submit_vote(voter_id=self.player.id, target_id=target)

# player_agent.py 수정 (✅)
mcp_tools.submit_vote(agent_id=self.player.id, target_id=target)
```

두 파일을 열어 실제 파라미터명을 확인하고 `agent_id` / `voter_id` 중 하나로 통일할 것.

---

#### C-11-3: `backend/game/roles.py` — FORTUNE_TELLER / SPY handler 누락

**증상**: `player_agent._allowed_ability_for_role()`에서 FORTUNE_TELLER → `"investigate"`, SPY → 능력 부여하는데 `ROLE_ABILITIES` 딕셔너리에 handler가 없어 능력 발동 시 아무 효과 없음.

**수정 내용**: `ROLE_ABILITIES`에 두 역할 handler 추가.

```python
# roles.py — 아래 두 핸들러 추가

def fortune_teller_divine(ctx: RoleAbilityContext) -> GameState:
    """점쟁이: 대상의 팀(마피아/시민)을 확인. 경찰과 동일하나 결과를 공개하지 않음."""
    if ctx.target:
        result = f"{ctx.target.name}은 {ctx.target.team.value}입니다. (점술 결과 — 비공개)"
        ctx.game_state.reports.append(Report(
            agent_id=ctx.actor.id, content=result, round=ctx.game_state.round
        ))
    return ctx.game_state

def spy_eavesdrop(ctx: RoleAbilityContext) -> GameState:
    """스파이: 밤 마피아 채팅 채널을 열람 (관찰 메모 저장)."""
    # 마피아 채널 메시지를 reports에 기록 (spy용 채널 열람 효과)
    mafia_chats = [
        msg for msg in ctx.game_state.chat_log
        if msg.get("channel") == "mafia_secret" and msg.get("round") == ctx.game_state.round
    ]
    summary = " | ".join(m.get("content", "") for m in mafia_chats) or "마피아 채팅 없음"
    ctx.game_state.reports.append(Report(
        agent_id=ctx.actor.id, content=f"[스파이 도청] {summary}", round=ctx.game_state.round
    ))
    return ctx.game_state

# ROLE_ABILITIES 딕셔너리에 추가
ROLE_ABILITIES = {
    ...기존...,
    Role.FORTUNE_TELLER: fortune_teller_divine,
    Role.SPY: spy_eavesdrop,
}
```

> `GameState.chat_log` 실제 필드명은 코드에서 확인 후 맞게 조정할 것.

---

## ~~🔄 진행 중 작업~~ ✅ 완료 (C-2, C-7, C-8, C-9, C-10)

### ~~[C-2]~~ ✅ MCP bind_tools + ToolNode 연동 완료 (`91150e0`)

**현황**: `player_agent.py`에 `bind_tools` 적용하여 tool_calls 있으면 `_decision_from_tool_calls()`로 처리함.  
하지만 **`graph.py`에서 MCPGameTools 직접 호출(수동 파이프라인)은 여전히 유지 중**.  
완전한 ReAct 패턴: **LLM이 Tool을 선택 → ToolNode 실행 → LLM엔게 결과 반환** 루프는 아직 미완.

**다음 단계 목표**:
```python
# graph.py
# 1. MCPGameTools를 @tool 함수로 래핑
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

@tool
def send_chat(agent_id: str, content: str, channel: str = "global") -> bool:
    """채팅 메시지를 전송한다."""
    return self.mcp_tools.send_chat(agent_id=agent_id, content=content, channel=channel)

@tool
def submit_vote(agent_id: str, target_id: str) -> bool:
    """투표 대상을 제출한다."""
    return self.mcp_tools.submit_vote(agent_id=agent_id, target_id=target_id)

# 2. graph.py에 ToolNode 추가
game_tools = [send_chat, submit_vote, use_ability]
tool_node = ToolNode(game_tools)

# 3. StateGraph에 tool_node 노드 추가
# agent → tool_calls 있으면 → tool_node → agent (루프)
```

**현재 player_agent.py의 `bind_tools`는 단발 호출로만 동작함.  
graph.py에서 ToolNode 루프를 연결하는 것이 목표.**

**참조**: `AGENT_DESIGN.md` §2.2, `EVALUATION_REFLECTION.md` §평가 요소 2: Tool Calling 자율성

---

## ~~🔄 현재 작업~~ ✅ C-5 완료 — 잔존 작업 없음

### ~~[C-5]~~ ✅ Redis Checkpointer 전면 연동 완료 (`5b557a0`)

**현황**: `MAFIA_USE_REDIS_CHECKPOINTER=1`일 때만 RedisSaver 사용, 실패 시 일반 compile 폴백.  
docker-compose에 `MAFIA_USE_REDIS_CHECKPOINTER=1` 설정되어 있음 (Claude 처리).

**확인 사항**:
```python
# _compile_agent_graph()가 실행할 때
# 1. RedisSaver가 정상 연결되는지 로그 확인
# 2. setup() 호출 성공 여부
# 3. ainvoke에 config={"configurable": {"thread_id": ...}}이 설정되는지
```

**폴백 제거**: Redis 연결 실패 시 로그를 남기고 실패 원인 보고.

**참조**: `RAG_AND_STORAGE_DESIGN.md` §4 Redis 키 설계

---

### ~~[C-8]~~ ✅ 슈퍼바이저 재진단 루프 완료 (`96becae`)

**현황**: Phase 종료 후 슈퍼바이저가 상황을 재진단하는 `supervisor_replan` 노드가 미구현 상태.

**목표**: `AGENT_DESIGN.md` §3.1 기반 구현
```python
# graph.py — supervisor_replan 노드 추가
def supervisor_replan(state: GameState) -> GameState:
    """각 Phase 종료 후 슈퍼바이저가 상황 재진단"""
    # 1. 이번 라운드 발언/투표 패턴 분석
    # 2. trust_score 재계산
    # 3. 정보 갭 확인 (경찰 조사 여부, 의사 침묵 등)
    # 4. 필요 시 새 directive 발행 → Redis 저장
    ...

# StateGraph에 노드 연결
# day_chat → supervisor_replan → win_condition_checker → 다음 Phase
```

**참조**: `AGENT_DESIGN.md` §3.1 슈퍼바이저 재진단 루프

---

## ~~🟡 중간 우선순위 작업~~ ✅ 완료 (C-7, C-9, C-10)

### ~~[C-7]~~ ✅ game/roles.py 능력 로직 완료 (`3af6d3c`)

**현황**: `detective_investigate`, `doctor_protect`, `mafia_attack`, `killer_piercing_attack` 함수가 시그니처만 있고 실제 로직 없음.

```python
def detective_investigate(ctx: RoleAbilityContext) -> GameState:
    if ctx.target:
        result = f"{ctx.target.name}은 {ctx.target.team.value}입니다."
        ctx.game_state.reports.append(Report(
            agent_id=ctx.actor.id, content=result, round=ctx.game_state.round,
        ))
    return ctx.game_state

def doctor_protect(ctx: RoleAbilityContext) -> GameState:
    if ctx.target:
        ctx.target.ability_used = True  # protected 플래그
    return ctx.game_state

def mafia_attack(ctx: RoleAbilityContext) -> GameState:
    if ctx.target and not ctx.target.ability_used:  # 보호 중 아닐 때만
        ctx.target.is_alive = False
        ctx.game_state.events.append(GameEvent(
            type="player_death",
            payload={"player": ctx.target.name, "role": ctx.target.role.value,
                     "cause": "mafia", "round": ctx.game_state.round}
        ))
    return ctx.game_state
```

**참조**: `GAME_RULES.md` §2 직업 명세

---

### ~~[C-9]~~ ✅ RAG 지식문서 ChromaDB 인덱싱 완료 (`c77e002`)

**배경**: Claude가 `docs/rag_knowledge/` 아래 RAG 지식 문서 20개 작성 완료.
이 문서들을 ChromaDB에 인덱싱해서 Agent가 `search_strategy_rag_tool`로 검색할 수 있게 해야 함.

**파일 구조**:
```
docs/rag_knowledge/
├── strategies/      # 7개: 직업별 전략
├── speech_patterns/ # 6개: 발언 스타일별 예시
├── situations/      # 6개: 상황별 대응
└── rules/           # 2개: 룰 문서 (Agent 조회용)
```

**작업 목표**:
```python
# backend/rag/store.py 또는 indexer.py
# docs/rag_knowledge/ 아래 모든 .md 파일을 읽어 ChromaDB에 인덱싱

import os
from pathlib import Path

def index_knowledge_base(knowledge_dir: str = "docs/rag_knowledge"):
    """docs/rag_knowledge/ 아래 .md 파일을 ChromaDB에 인덱싱"""
    for md_file in Path(knowledge_dir).rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        metadata = {
            "category": md_file.parent.name,   # strategies, speech_patterns, situations, rules
            "filename": md_file.stem,
            "filepath": str(md_file),
        }
        # 파일 상단 frontmatter에서 role, team, speech_style 등 메타데이터 파싱
        # ChromaDB collection.add(documents=[content], metadatas=[metadata])
```

**메타데이터 파싱**: 각 .md 파일 상단에 `category`, `role`, `team`, `speech_style` 등이 있으니 파싱해서 ChromaDB 메타데이터에 포함.

**검색 필터 연동**: `RAG_AND_STORAGE_DESIGN.md` §3.2 메타데이터 필터 설계 참조.

**참조**: `docs/rag_knowledge/` 전체, `RAG_AND_STORAGE_DESIGN.md` §3, `AGENT_DESIGN.md` §5

---

### ~~[C-10]~~ ✅ GameInsightAgent 완료 (`e531163`~`d691e80`)

**배경**: 현재 RAG 지식베이스는 정적 `.md` 파일 20개로만 구성됨.
게임이 진행될수록 실전 전략·발언·투표 패턴을 자동 학습해 Agent 품질을 지속 향상시키는 파이프라인이 필요.

**데이터 파이프라인**:
```
GameEngine (GameState) → [게임 종료 hook]
  → Redis mafia:game_archive:{game_id}  (TTL 30일)
  → GameInsightAgent (LangGraph ReAct)
  → RAGStore.add_documents(source="runtime")
  → ChromaDB  ai_mafia_knowledge 컬렉션
```

---

#### 8-1: `backend/game/archiver.py` — 신규 생성

```python
import json
import redis
from backend.game.state import GameState  # 실제 임포트 경로 확인

class GameArchiver:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def archive(self, state: GameState) -> None:
        """게임 종료 시 GameState를 Redis에 JSON으로 저장 (TTL 30일)"""
        key = f"mafia:game_archive:{state.game_id}"
        self.redis.setex(key, 60 * 60 * 24 * 30, state.model_dump_json())
```

---

#### 8-2: `backend/agents/analysis_agent.py` — 신규 생성

**StateGraph 구조**:
```
[load_pending] → [analyze] ──(tool_calls 루프)──→ [write_rag] → [mark_done] → END
```

**상태 스키마**:
```python
from typing import TypedDict, List, Optional
from langchain_core.messages import BaseMessage

class _InsightState(TypedDict):
    pending_game_ids: List[str]     # 미분석 game_id 목록
    current_game: Optional[dict]    # 현재 분석 중인 GameState JSON
    generated_docs: List[dict]      # 생성된 RAG 문서 버퍼
    messages: List[BaseMessage]     # LLM 메시지 히스토리 (ReAct)
```

**bind_tools 도구 3개**:
```python
from langchain_core.tools import tool

@tool
def read_game_record(game_id: str) -> str:
    """Redis에서 완료된 게임 기록을 읽는다."""
    key = f"mafia:game_archive:{game_id}"
    data = redis_client.get(key)
    return data.decode() if data else "게임 기록 없음"

@tool
def search_existing_rag(query: str) -> str:
    """기존 RAG에서 유사 문서를 검색해 중복 생성을 방지한다."""
    docs = rag_store.similarity_search(query, k=3)
    return "\n\n".join(d.page_content for d in docs)

@tool
def write_insight_doc(title: str, category: str, content: str, tags: str) -> str:
    """분석 결과 문서를 RAGStore에 추가한다.
    category: strategy | situation | speech_pattern | rule
    tags: 쉼표 구분 문자열
    """
    rag_store.add_documents([{
        "page_content": content,
        "metadata": {
            "title": title,
            "category": category,
            "tags": tags,
            "source": "runtime",
        }
    }])
    return f"문서 추가 완료: {title}"
```

**with_structured_output 스키마**:
```python
from pydantic import BaseModel
from typing import Literal

class GameInsight(BaseModel):
    title: str
    category: Literal["strategy", "situation", "speech_pattern"]
    content: str          # 마크다운 형식 인사이트 본문
    tags: List[str]
    source_game_id: str
    insight_type: str     # "winning_pattern" | "speech_pattern" | "voting_pattern"
```

**시스템 프롬프트 핵심**:
- 게임 채팅 로그, 투표 기록, 생존 플레이어, 승리팀을 분석
- 승리 팀이 사용한 전략 패턴 추출
- `search_existing_rag`로 기존 RAG와 중복 여부 확인 후 새 인사이트만 생성
- 1판당 최대 2~3개 문서 생성
- 문서 생성 후 `write_insight_doc` 도구 호출

**노드 구현 핵심**:
```python
# load_pending 노드
def load_pending(state: _InsightState) -> _InsightState:
    """Redis SET에서 미분석 game_id 목록을 로드"""
    processed = redis_client.smembers("mafia:game_analysis:processed")
    all_keys = redis_client.keys("mafia:game_archive:*")
    pending = [
        k.decode().split(":")[-1] for k in all_keys
        if k.decode().split(":")[-1].encode() not in processed
    ]
    return {**state, "pending_game_ids": pending}

# mark_done 노드
def mark_done(state: _InsightState) -> _InsightState:
    """분석 완료된 game_id를 SET에 추가"""
    if state.get("current_game"):
        gid = state["current_game"].get("game_id", "")
        if gid:
            redis_client.sadd("mafia:game_analysis:processed", gid)
    return state
```

---

#### 8-3: `backend/game/runner.py` — 게임 종료 hook 추가

`_check_game_end()` 또는 `run()` 루프 내 승리 조건 확정 직후에 추가:

```python
# 기존 게임 종료 처리 후
if self.engine.state.winner is not None:
    archiver.archive(self.engine.state)                        # Redis 아카이브
    asyncio.create_task(insight_agent.run())                   # 백그라운드 분석
```

- `archiver`는 `GameRunner.__init__`에서 `GameArchiver(redis_client)` 로 초기화
- `insight_agent`는 `GameInsightAgent(redis_client, rag_store)` 로 초기화

---

#### 8-4: `backend/rag/store.py` — `source="runtime"` 메타데이터 구분 (선택)

기존 `add_documents()` 호출 시 메타데이터에 `"source": "runtime"` 이 포함되면 충분.
별도 메서드 추가 불필요. 필요 시 검색 필터에서 `source` 기준 분리 가능:

```python
# source=runtime 문서만 검색
docs = collection.query(where={"source": "runtime"}, ...)

# 정적 지식베이스만 검색
docs = collection.query(where={"source": "static"}, ...)
```

기존 지식문서 인덱싱(C-9) 시 `"source": "static"` 메타데이터를 함께 넣어둘 것.

---

**검증 방법**:
```bash
# 1. 테스트 게임 아카이브 수동 삽입
redis-cli set mafia:game_archive:test_001 '{"game_id":"test_001","winner":"mafia","chat_log":[...]}'

# 2. GameInsightAgent.run() 단독 실행 후 ChromaDB 문서 수 증가 확인

# 3. RAGStore 검색으로 실전 데이터 문서 포함 여부 확인
rag_store.similarity_search("마피아 2인 열세 역전 전략")
```

**참조**: `RAG_AND_STORAGE_DESIGN.md` §8, `AGENT_DESIGN.md` §2.2, `TASK_PLAN.md` Phase 8

---

## 📢 인프라 보고 방법

docker-compose.yml 변경이 필요하면 **직접 수정 말고** Claude에게 보고:
```
[인프라 보고] 항목
요청: 환경변수 FOO=bar 추가 / 포트 변경 / 기타
이유: ...
```

---

## ✅ 완료 보고 형식

```
[완료] C-N — 작업명
구현 내용: ...
설계와 다르게 구현한 부분: ...
Claude에게 요청 필요한 사항: ...
```

---

## 📋 참조 문서

| 문서 | 참조 이유 |
|------|----------|
| `AGENT_DESIGN.md` | Agent Node 구조, MCP Tool |
| `EVALUATION_REFLECTION.md` | bind_tools 패턴, Structured Output |
| `RAG_AND_STORAGE_DESIGN.md` | Redis 키 설계 |
| `TECH_ARCHITECTURE.md` | WebSocket 이벤트 계약, 채널 분리 |
| `GAME_RULES.md` | 직업 능력 상세 |
