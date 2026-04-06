# ⚙️ Cursor 작업 지시서 (WORK_ORDER_CURSOR)

> **대상**: Cursor AI — 백엔드 개발자
> **작성자**: Claude AI (기획자 + 인프라)
> **최종 업데이트**: 2026-04-06 (C-19 완료, C-20 신규 — trust_score·player ID 통일)

> 작업 전 반드시 이 문서를 먼저 읽을 것.  
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
| C-12-1 | `backend/config.py` — LLM_CONFIG + `get_chat_llm()` 팩토리 | `f25160f` |
| C-12-2 | `player_agent.py` — `get_chat_llm()` 교체 | `f25160f` |
| C-12-3 | `analysis_agent.py` — `get_chat_llm()` 교체 | `f25160f` |
| C-12-4 | `GET /health` — `llm_provider` 필드 추가 | `f25160f` |
| C-13 | 전역 로깅 + LangSmith(`LANGCHAIN_TRACING_V2`) verbose/debug | 2026-04-06 |
| C-14 | graph/tools/store/player_agent 가드·예외·RAG 경고 로깅 | 2026-04-06 |
| C-15 | 멀티 POD 소유권 로깅 (`pod.py`, lifespan, registry, graph, runner) | 2026-04-06 |
| C-16 | G-12 RAG 디버그 패널 — `AgentOutput.rag_context`, `snapshot.py`, `runner.py` 연동 | 2026-04-06 |
| C-17 | Phase 5-8 슈퍼바이저 MCP — `_choose_suspect()` report 활용, `_issue_directives_for_phase()` reports 전달 | 2026-04-06 |
| C-18 | Phase 6-7 AI vs AI 시뮬 테스트 + `test_mcp_memory_tools.py` 삭제 | 2026-04-06 |

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

#### C-10-1: `backend/game/archiver.py` — 신규 생성

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

#### C-10-2: `backend/agents/analysis_agent.py` — 신규 생성

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

#### C-10-3: `backend/game/runner.py` — 게임 종료 hook 추가

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

#### C-10-4: `backend/rag/store.py` — `source="runtime"` 메타데이터 구분 (선택)

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

---

## ~~🔴 신규 긴급 작업~~ ✅ C-13 / C-14 완료 (2026-04-06)

### ~~[C-13]~~ ✅ 전역 로깅 + LangSmith 트레이싱

- `main.py`: 앱 생성 전 `logging.basicConfig`, `LANGCHAIN_TRACING_V2=true` 시 `set_debug`/`set_verbose` + `mafia.main` 로그 (임포트 실패 시 WARNING).
- `graph.py` / `player_agent.py` / `runner.py` / `retriever.py`: 지시서 표에 따른 INFO/DEBUG 로그.

### ~~[C-14]~~ ✅ 가드코드 + 예외 표준화

- `graph.py` `_run_agent_node`: 빈/미등록 `agent_id` → `ValueError`.
- `mcp/tools.py` `get_my_role`: `next(..., None)` + `ValueError`.
- `rag/store.py` `similarity_search`: `count`/`query` 실패 시 `logger.warning`.
- `player_agent.py`: LangChain 메시지 임포트 → `ImportError` 전용 처리.

**검증**: `pytest tests/ --ignore=tests/test_mcp_memory_tools.py` (51 passed).  
※ `test_mcp_memory_tools.py`는 `AgentMemory` 미정의로 수집 단계에서 실패 — 별도 정리 필요.

---

### ~~[C-15]~~ ✅ 멀티 POD 소유권 로깅 (2026-04-06)

- **C-15-1** `backend/pod.py`: `MAFIA_POD_ID` → 없으면 `socket.gethostname()`, 모듈 상수 `POD_ID`.
- **C-15-2** `main.py`: FastAPI `lifespan`으로 기동/종료 시 `pod_id`, `REDIS_URL`, `MAFIA_USE_REDIS_CHECKPOINTER`, `MAFIA_LLM_PROVIDER` 로깅.
- **C-15-3** `registry.py`: `create_game` 성공 INFO, `get` 미스 시 WARNING (`mafia.registry`).
- **C-15-4** `graph.py` `__init__`: AgentGraph + supervisor 3종 + agent 키 목록 INFO.
- **C-15-5** `runner.py`: `run()` 시작 INFO, 루프마다 `Phase 전환` INFO, `advance_phase` 직후 INFO(기존 phase 로그를 POD 접두로 통합), 승리 확정 시 `게임 종료` INFO.
- **C-15-6** `graph.py` `_issue_directives_for_phase`: 발행 시작 INFO + Citizen/Mafia/Neutral(밤능력 분기 포함) DEBUG.

**설계 대비 보완**: 지시서 예시의 `run()` 종료 로그는 루프 내부 `winner` 확정 직후에 남기도록 함(기존 구조상 `while` 이후에 도달하지 않음).

**인프라**: `MAFIA_POD_ID`·Sticky Session은 Claude/docker-compose 담당.

---

## ~~🔴 신규 작업~~ ✅ C-16/C-17/C-18 완료 (2026-04-06)

---

## 🔴 신규 작업 (2026-04-06 — README 점검)

### [C-19] `backend/README.md` 최신화

> **배경**: 루트 README 점검 결과 backend/README.md에 다음 항목이 누락/오래됨.
> Cursor 담당 파일이므로 직접 수정 지시.

#### 수정 항목 3가지

**① 환경변수 테이블에 4개 추가**

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `LANGCHAIN_TRACING_V2` | `false` | `true` 설정 시 LangSmith 트레이싱 활성화 |
| `LANGCHAIN_API_KEY` | — | LangSmith API 키 (`TRACING_V2=true` 시 사용) |
| `LANGCHAIN_PROJECT` | `mafia-game` | LangSmith 프로젝트 이름 |
| `MAFIA_POD_ID` | — | 멀티POD 환경 식별자 (미설정 시 hostname 자동 사용) |

**② `agents/` 디렉토리 구조에 `analysis_agent.py` 추가**

```
agents/
├── graph.py           ← LangGraph AgentGraph
├── player_agent.py    ← 개별 AI Agent (LLM 연동)
├── analysis_agent.py  ← GameInsightAgent (게임 결과 RAG 자기학습)  ← 추가
├── pool.py
└── persona.py
```

**③ `MAFIA_USE_REDIS_CHECKPOINTER` 기본값 설명 명확화**

```markdown
# 현재 (❌ 혼동 유발)
| MAFIA_USE_REDIS_CHECKPOINTER | 0 | ...

# 수정 (✅)
| MAFIA_USE_REDIS_CHECKPOINTER | 0 (로컬) / 1 (docker-compose 자동) | ...
```

**완료 보고 형식**:
```
[완료] C-19 — backend/README.md 최신화
구현 내용: ...
```

---

## ~~🔴 신규 작업 (2026-04-06 — WORK_TASK_GEMINI 보고 반영)~~

### [C-16] G-12 RAG 디버그 패널 — 백엔드 rag_context 연동

> **배경**: Gemini가 `components/status_panel.py`에 RAG 디버그 패널 UI(G-12)를 구현 완료했으나,
> 백엔드가 `game_state_update` WebSocket 이벤트에 `rag_context`를 포함하지 않아
> 프론트에서 "RAG 컨텍스트 없음"만 표시됨.

#### C-16-1: `backend/agents/player_agent.py` — AgentOutput에 rag_context 추가

```python
# 현재 AgentOutput
@dataclass
class AgentOutput:
    speech: Optional[str]
    action: Optional[dict]
    vote: Optional[str]
    internal_notes: Optional[str]

# 수정: rag_context 필드 추가
@dataclass
class AgentOutput:
    speech: Optional[str]
    action: Optional[dict]
    vote: Optional[str]
    internal_notes: Optional[str]
    rag_context: list[dict] = field(default_factory=list)  # RAG 참조 문서 목록
```

`PlayerAgent.run()` 내부에서 `rag_context` 값을 `AgentOutput`에 포함하여 반환할 것.

#### C-16-2: `backend/game/snapshot.py` — rag_context 페이로드 포함

`build_game_state_payload()` 함수가 `rag_context` 인자를 받아 페이로드에 포함하도록 확장.

```python
def build_game_state_payload(state: GameState, rag_context: list[dict] | None = None) -> dict:
    payload = { ...기존 필드... }
    if rag_context:
        payload["rag_context"] = rag_context  # 최근 에이전트가 참조한 RAG 문서
    return payload
```

#### C-16-3: `backend/game/runner.py` — 에이전트 실행 결과에서 rag_context 수집 후 브로드캐스트

```python
# runner.py — 에이전트 라운드 실행 후
outputs: dict[str, AgentOutput] = await self.agent_graph.run_day_chat_round(state)

# 최근 에이전트들의 rag_context 수집 (마지막 에이전트 기준 또는 합산)
latest_rag_context = []
for output in outputs.values():
    if output.rag_context:
        latest_rag_context = output.rag_context  # 마지막 에이전트 RAG 사용
        break

# game_state_update 브로드캐스트에 rag_context 포함
payload = build_game_state_payload(state, rag_context=latest_rag_context)
await self.ws_manager.broadcast(self.game_id, {"event": "game_state_update", "payload": payload})
```

**검증 방법**:
```bash
# 게임 실행 후 game_state_update WebSocket 이벤트 payload에 rag_context 배열 포함 확인
# 프론트 RAG 디버그 패널에 문서 제목/점수 표시 확인
```

---

### [C-17] Phase 5-8 — 슈퍼바이저 MCP 연동

> **배경**: `TASK_PLAN.md` Phase 5-8 미구현 상태.
> 현재 PlayerAgent는 MCP Tool을 직접 호출하지만 Supervisor는 MCP 미연결 상태.
> Supervisor가 `report_to_supervisor` 도구를 통해 Agent 보고를 수신하는 구조 완성이 목표.

#### 구현 목표

현재 `mcp/tools.py`의 `report_to_supervisor()` 도구가 `GameState.reports`에 추가까지만 되어 있음.
Supervisor가 이 `reports`를 실제로 읽어서 다음 Phase 지시에 반영하는 루프 완성.

```python
# supervisors/citizen.py — issue_directives()
def issue_directives(self, state: GameState, reports: List[Report]) -> List[Directive]:
    # 현재: reports 파라미터를 받지만 활용 여부 불명확
    # 목표: reports에서 의심 정보 추출 → suspect 선정 로직에 반영
    
    # 예시: 경찰 보고서에서 마피아 확인 정보 우선 반영
    confirmed_mafia = [
        r for r in reports
        if "마피아" in r.content and r.round == state.round - 1
    ]
    if confirmed_mafia:
        # 확인된 마피아를 표적으로 지시
        ...
```

**확인할 것**:
1. `graph.py`의 `_issue_directives_for_phase()`에서 `reports`를 실제로 Supervisor에 전달하는지 확인
2. 전달 안 되면 `state.reports`를 넘기도록 수정
3. 각 Supervisor의 `issue_directives(reports)` 활용 로직 구현

**참조**: `AGENT_DESIGN.md` §2.2 MCP Tool, `WORK_ORDER_CURSOR.md` C-2 완료 내역

---

### [C-18] Phase 6-7 AI vs AI 시뮬레이션 테스트 + test_mcp_memory_tools.py 정리

> **배경**: `TASK_PLAN.md` Phase 6-7 미작성 + `test_mcp_memory_tools.py`가
> `AgentMemory` 미정의로 pytest 수집 단계에서 실패 중.
> `pytest tests/ --ignore=tests/test_mcp_memory_tools.py`로 우회 중이나 정리 필요.

#### C-18-1: `backend/tests/test_mcp_memory_tools.py` — 파일 삭제 또는 skip 처리

`AgentMemory` 클래스가 현재 코드베이스에 존재하지 않음. 두 가지 선택:
- **선택 A (권장)**: 파일 삭제 — 미구현 기능의 테스트이므로 제거
- **선택 B**: 파일 상단에 `pytest.importorskip` 또는 `@pytest.mark.skip` 적용

```python
# 선택 B 예시
import pytest
pytestmark = pytest.mark.skip(reason="AgentMemory 미구현 — Phase 9 예정")
```

#### C-18-2: `backend/tests/test_ai_simulation.py` — AI vs AI 헤드리스 시뮬레이션 테스트 신규 작성

`MAFIA_USE_LLM=0` 환경에서 AI끼리 게임을 완주하는 스모크 테스트:

```python
# test_ai_simulation.py
import pytest
import asyncio
from backend.game.runner import GameRunner
from backend.game.engine import GameEngine
# ...

@pytest.mark.asyncio
async def test_ai_vs_ai_full_game():
    """AI 전원(6인) 게임이 최대 10라운드 내 정상 종료되는지 확인"""
    engine = GameEngine(...)
    runner = GameRunner(engine=engine, ...)
    
    await asyncio.wait_for(runner.run(), timeout=60)  # 60초 타임아웃
    
    assert engine.state.winner is not None, "게임이 승리 조건 없이 종료됨"
    assert engine.state.winner in ("mafia", "citizen", "neutral")
```

**참조**: `backend/tests/test_mcp_memory_tools.py` 기존 패턴, `TASK_PLAN.md` Phase 6-7

**검증 방법**:
```bash
MAFIA_USE_LLM=0 pytest backend/tests/ -v
# test_mcp_memory_tools.py 관련 에러 없이 전체 통과 확인
```

**완료 보고 형식**:
```
[완료] C-16 — rag_context 백엔드 연동
[완료] C-17 — 슈퍼바이저 MCP report 활용
[완료] C-18 — AI vs AI 시뮬 테스트 + test_mcp_memory_tools 정리
구현 내용: ...
설계와 다르게 구현한 부분: ...
Claude에게 요청 필요한 사항: ...
```

---

## 📢 인프라 보고 방법

docker-compose.yml 변경이 필요하면 **직접 수정 말고** Claude에게 보고:
```
[인프라 보고] 항목
요청: 환경변수 FOO=bar 추가 / 포트 변경 / 기타
이유: ...
```

---

## ~~🆕 신규 작업~~ ✅ C-12 완료

### ~~[C-12]~~ ✅ LLM Provider config 레이어 완료 (`f25160f`)

> **배경**  
> 현재 백엔드는 `ANTHROPIC_API_KEY` + `ChatAnthropic` 단일 경로만 지원.  
> 과제 제출 환경은 **Azure OpenAI** (`AOAI_*` 환경변수)로 LLM을 주입한다.  
> docker-compose 실행 시 환경변수만 바꾸면 Provider가 전환되도록 config 레이어를 추가한다.  
> **docker-compose.yml / .env.example 수정은 Claude 담당** — Cursor는 백엔드 코드만 수정.

---

#### C-12-1: `backend/config.py` — LLM config 중앙화 (신규 생성)

환경변수를 한 곳에서 읽어 `LLM_CONFIG` 딕셔너리로 제공한다.

```python
# backend/config.py
import os

# ---------------------------------------------------------
# LLM Provider 선택
# MAFIA_LLM_PROVIDER=anthropic (기본) | azure
# ---------------------------------------------------------
LLM_PROVIDER = os.getenv("MAFIA_LLM_PROVIDER", "anthropic").lower()

LLM_CONFIG: dict = {
    "provider": LLM_PROVIDER,

    # Anthropic
    "anthropic_api_key":  os.getenv("ANTHROPIC_API_KEY", "").strip(),
    "anthropic_model":    os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4"),

    # Azure OpenAI
    "aoai_endpoint":      os.getenv("AOAI_ENDPOINT", "").strip(),
    "aoai_api_key":       os.getenv("AOAI_API_KEY", "").strip(),
    "aoai_api_version":   os.getenv("AOAI_API_VERSION", "2024-02-01"),
    "aoai_deploy_chat":   os.getenv("AOAI_DEPLOY_GPT4O", "").strip(),      # 기본 chat 모델
    "aoai_deploy_mini":   os.getenv("AOAI_DEPLOY_GPT4O_MINI", "").strip(), # 경량 모델 (선택)
    "aoai_deploy_embed":  os.getenv("AOAI_DEPLOY_EMBED_3_LARGE", "").strip(),
}

def is_llm_enabled() -> bool:
    """LLM 활성화 여부 (MAFIA_USE_LLM=0 이면 False)"""
    return os.getenv("MAFIA_USE_LLM", "1") != "0"

def get_chat_llm(temperature: float = 0):
    """
    Provider에 따라 LangChain Chat LLM 객체를 반환한다.
    키가 없으면 None 반환 → 호출부에서 Fallback 처리.
    """
    if not is_llm_enabled():
        return None

    if LLM_CONFIG["provider"] == "azure":
        api_key  = LLM_CONFIG["aoai_api_key"]
        endpoint = LLM_CONFIG["aoai_endpoint"]
        deploy   = LLM_CONFIG["aoai_deploy_chat"]
        if not (api_key and endpoint and deploy):
            return None
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint     = endpoint,
            api_key            = api_key,
            azure_deployment   = deploy,
            openai_api_version = LLM_CONFIG["aoai_api_version"],
            temperature        = temperature,
        )
    else:  # anthropic (기본)
        api_key = LLM_CONFIG["anthropic_api_key"]
        if not api_key:
            return None
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model       = LLM_CONFIG["anthropic_model"],
            api_key     = api_key,
            temperature = temperature,
        )
```

---

#### C-12-2: `backend/agents/player_agent.py` — `get_chat_llm()` 교체

기존 `os.getenv("ANTHROPIC_API_KEY")` 직접 호출을 `config.get_chat_llm()` 으로 교체한다.

```python
# 기존 (❌)
api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
if not api_key:
    return self._fallback_decision(state)
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model=model_name, temperature=0, api_key=api_key)

# 수정 (✅)
from backend.config import get_chat_llm
llm = get_chat_llm(temperature=0)
if llm is None:
    return self._fallback_decision(state)
```

---

#### C-12-3: `backend/agents/analysis_agent.py` — `get_chat_llm()` 교체

동일하게 `os.getenv("ANTHROPIC_API_KEY")` 2곳을 `get_chat_llm()` 으로 교체한다.

---

#### C-12-4: `GET /health` — provider 정보 포함

`main.py`의 `/health` 응답에 현재 LLM provider 정보를 추가한다.

```python
# 기존
{ "status": "ok", "rag_status": "ok" }

# 수정
{ "status": "ok", "rag_status": "ok", "llm_provider": "azure" }
# llm_provider: "anthropic" | "azure" | "disabled"
```

`llm_provider` 값 결정 로직:
- `MAFIA_USE_LLM=0` → `"disabled"`
- `MAFIA_LLM_PROVIDER=azure` + 키 있음 → `"azure"`
- `MAFIA_LLM_PROVIDER=anthropic` + 키 있음 → `"anthropic"`
- 키 없음 → `"fallback"`

---

#### Claude 담당 (Cursor 수정 불필요)

아래는 **Claude가 직접 처리**한다. Cursor는 건드리지 않는다:

```
# .env.example 추가 항목 (Claude 처리)
MAFIA_LLM_PROVIDER=anthropic   # anthropic | azure

# Azure OpenAI (MAFIA_LLM_PROVIDER=azure 시 사용)
AOAI_ENDPOINT=
AOAI_API_KEY=
AOAI_API_VERSION=2024-02-01
AOAI_DEPLOY_GPT4O=
AOAI_DEPLOY_GPT4O_MINI=
AOAI_DEPLOY_EMBED_3_LARGE=
AOAI_DEPLOY_EMBED_3_SMALL=
AOAI_DEPLOY_EMBED_ADA=

# docker-compose.yml environment 섹션에 MAFIA_LLM_PROVIDER 등 pass-through 추가
```

---

**검증 방법**:
```bash
# Anthropic 모드 (기존)
MAFIA_LLM_PROVIDER=anthropic docker-compose up --build
curl http://localhost:8000/health
# → { "llm_provider": "anthropic" }

# Azure 모드
MAFIA_LLM_PROVIDER=azure AOAI_API_KEY=... AOAI_ENDPOINT=... docker-compose up --build
curl http://localhost:8000/health
# → { "llm_provider": "azure" }

# Fallback 모드
MAFIA_USE_LLM=0 docker-compose up --build
curl http://localhost:8000/health
# → { "llm_provider": "disabled" }
```

**참조**: `.env.example`, `docker-compose.yml`

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
