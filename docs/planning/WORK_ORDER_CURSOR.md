# ⚙️ Cursor 작업 지시서 (WORK_ORDER_CURSOR)

> **대상**: Cursor AI — 백엔드 개발자  
> **작성자**: Claude AI (기획자 + 인프라)  
> **최초 작성일**: 2026-03-19  
> **최종 업데이트**: 2026-03-19 (af1a977 반영)

> 작업 전 반드시 `ROLE_CURSOR.md`와 이 문서를 먼저 읽을 것.
> **docker-compose.yml은 수정하지 않는다** — Claude 담당.

---

## ✅ 완료된 작업

| 항목 | 내용 | 커밋 |
|------|------|------|
| C-1 | RAG → player_agent 프롬프트 연결 | `af1a977` |
| C-3 | 슈퍼바이저 전략 로직 (trust_score + 우선순위) | `af1a977` |
| C-6 | 발언 타이밍 딜레이 (`_speech_delay()`) | `af1a977` |
| — | NIGHT_MAFIA 라운드 신규 구현 (`run_night_mafia_round()`) | `af1a977` |
| — | Phase 가드 (허용 행동만 반환) | `af1a977` |
| — | CI/LLM 제어 플래그 (`MAFIA_USE_LLM=0`) | `af1a977` |

---

## 🔴 긴급 작업 (미완료)

### [C-2] MCP bind_tools + ToolNode 패턴 적용

**현황**: `graph.py`에서 `MCPGameTools`를 직접 메서드 호출하고 있음.  
이는 파이프라인 방식으로 평가 기준 미달 (`EVALUATION_REFLECTION.md` 참조).

**목표**: LLM이 Tool을 스스로 선택하는 ReAct 패턴 적용.

**구체적 작업**:
```python
# 현재 (❌ 수동 호출)
if output.speech:
    self.mcp_tools.send_chat(agent_id=agent_id, content=output.speech)

# 목표 (✅ bind_tools + ToolNode)
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

@tool
def send_chat(agent_id: str, content: str, channel: str = "global") -> bool:
    """채팅 메시지를 전송한다."""
    ...

tools = [send_chat, submit_vote, use_ability, get_game_state, search_rag, ...]
agent_llm = llm.bind_tools(tools)
tool_node = ToolNode(tools)

# graph: agent_node → (tool_calls 있으면) → tool_node → agent_node
```

**참조 문서**: `AGENT_DESIGN.md` §2.2, `EVALUATION_REFLECTION.md` §평가요소2

---

### [C-4] 마피아 밤 채널 WebSocket 브로드캐스트 필터링

**현황**: `graph.py`의 `run_night_mafia_round()`에서 `mafia_secret` 채널로 전송하나,  
`websocket/manager.py`의 `broadcast()`가 채널 구분 없이 모든 클라이언트에게 전송.  
시민도 마피아 채팅을 볼 수 있는 상태.

**목표**: `mafia_secret` 채널 메시지는 마피아 역할 플레이어에게만 전송.

**구체적 작업**:
```python
# websocket/manager.py에 채널별 필터링 브로드캐스트 추가
async def broadcast_to_channel(
    self,
    game_id: str,
    message: ServerToClientEvent,
    channel: str,
    allowed_player_ids: list[str],  # 마피아 player_id 목록
) -> None:
    """
    channel == 'mafia_secret': allowed_player_ids에게만 전송
    channel == 'global': 전체 전송
    channel == 'spy_listen': allowed_player_ids(스파이) + 마피아에게 전송
    """
    ...

# runner.py 또는 engine에서
# NIGHT_MAFIA phase 진입 시 마피아 player_id 목록을 ws_manager에 전달
```

**참조 문서**: `TECH_ARCHITECTURE.md` §3.4 채팅 채널 분리

---

## 🟡 중간 우선순위 작업

### [C-5] Redis Checkpointer 연동

**현황**: `graph.py`에 `thread_id` config만 있고 실제 Redis Checkpointer 없음.  
Agent가 라운드 간 이전 관찰을 기억하지 못함.

**전제 조건**: `_DayChatState`에서 PlayerAgent 객체를 제거하고 agent_id만 전달하는 구조로 변경 필요 (비직렬화 객체 문제).

**구체적 작업**:
```python
from langgraph.checkpoint.redis import RedisSaver
import redis

# graph.py __init__
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
checkpointer = RedisSaver(redis_client)
self._agent_call_graph = day_chat_graph.compile(checkpointer=checkpointer)

# 각 Agent 호출 시
config = {"configurable": {"thread_id": f"{game_id}_{agent_id}"}}
await self._agent_call_graph.ainvoke(state, config=config)
```

> Redis 서버는 `docker-compose up redis`로 실행 (Claude가 docker-compose 관리).

**참조 문서**: `RAG_AND_STORAGE_DESIGN.md` §4 Redis 키 설계

---

### [C-7] game/roles.py 능력 로직 구현

**현황**: `detective_investigate`, `doctor_protect`, `mafia_attack`, `killer_piercing_attack` 함수가 시그니처만 있고 실제 로직 없음.

**구체적 작업**:
```python
def detective_investigate(ctx: RoleAbilityContext) -> GameState:
    # 대상의 team(mafia 여부) 확인 → 경찰 Agent 메모리에 기록
    # ctx.game_state.reports에 결과 추가
    if ctx.target:
        result = f"{ctx.target.name}은 {ctx.target.team.value}입니다."
        ctx.game_state.reports.append(Report(
            agent_id=ctx.actor.id,
            content=result,
            round=ctx.game_state.round,
        ))
    return ctx.game_state

def doctor_protect(ctx: RoleAbilityContext) -> GameState:
    # 대상 Player에 protected=True 임시 플래그 추가
    # mafia_attack 시 protected 체크하여 무효화
    if ctx.target:
        ctx.target.ability_used = True  # protected 플래그로 활용
    return ctx.game_state

def mafia_attack(ctx: RoleAbilityContext) -> GameState:
    # doctor가 보호 중이 아니면 is_alive = False
    # player_death 이벤트 GameState.events에 추가
    if ctx.target and not ctx.target.ability_used:  # ability_used = protected
        ctx.target.is_alive = False
        ctx.game_state.events.append(GameEvent(
            type="player_death",
            payload={"player": ctx.target.name, "role": ctx.target.role.value, "cause": "mafia", "round": ctx.game_state.round}
        ))
    return ctx.game_state
```

**참조 문서**: `GAME_RULES.md` §2 직업 명세

---

## ✅ 완료 보고 형식

작업 완료 후 Claude에게 아래 형식으로 보고:

```
[완료] C-N — 작업명

구현 내용:
- ...

설계와 다르게 구현한 부분 (있을 경우):
- ...

Claude에게 요청 필요한 사항 (docker-compose, docs 변경 등):
- ...
```

---

## 📋 참조 문서 목록

| 문서 | 참조 이유 |
|------|----------|
| `AGENT_DESIGN.md` | Agent Node 구조, 슈퍼바이저 전략, MCP Tool |
| `EVALUATION_REFLECTION.md` | bind_tools 패턴, Structured Output, 메모리 요구사항 |
| `RAG_AND_STORAGE_DESIGN.md` | Redis 키 설계, RAG 활용 기준 |
| `TECH_ARCHITECTURE.md` | WebSocket 이벤트 계약, 채널 분리 |
| `GAME_RULES.md` | 직업 능력 상세 |
