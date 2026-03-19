# ⚙️ Cursor 작업 지시서 (WORK_ORDER_CURSOR)

> **대상**: Cursor AI — 백엔드/인프라 담당  
> **작성자**: Claude AI (기획자)  
> **최초 작성일**: 2026-03-19  
> **기준 커밋**: `978c755`

> 작업 전 반드시 `ROLE_CURSOR.md`와 이 문서를 먼저 읽을 것.

---

## 🔴 긴급 작업 (즉시 처리)

### [C-1] RAG → player_agent 프롬프트 연결

**현황**: `rag/store.py` ChromaDB 구현은 완료됐으나, `player_agent.py`의 `_decide_with_llm()` 에서 RAG 쿼리를 전혀 호출하지 않음. RAG가 있어도 Agent 발언에 반영이 안 되는 상태.

**목표**: Agent가 발언/투표 결정 전 RAG를 조회하고 결과를 프롬프트 컨텍스트로 주입.

**구체적 작업**:
```
player_agent.py → _decide_with_llm() 내부
  1. RAGStore 인스턴스를 주입받거나 싱글턴으로 접근
  2. 현재 상황 기반 쿼리 생성
     예: f"라운드 {round}, {my_role} 역할, {phase} 상황 전략"
  3. similarity_search(query, k=3) 호출
  4. 결과를 human_prompt의 "rag_context" 필드에 추가
```

**참조 문서**: `AGENT_DESIGN.md` §5 RAG 설계, `RAG_AND_STORAGE_DESIGN.md`

---

### [C-2] MCP bind_tools + ToolNode 패턴 적용

**현황**: `graph.py`에서 `MCPGameTools`를 직접 메서드 호출(`self.mcp_tools.send_chat(...)`)하고 있음. 이는 파이프라인 방식으로 평가 기준 미달.

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

tools = [send_chat, submit_vote, use_ability, get_game_state, ...]
agent_llm = llm.bind_tools(tools)
tool_node = ToolNode(tools)

# graph: agent_node → (tool_calls 있으면) → tool_node → agent_node
```

**참조 문서**: `AGENT_DESIGN.md` §2.2, `EVALUATION_REFLECTION.md` §평가요소2

---

### [C-3] 슈퍼바이저 전략 로직 고도화

**현황**: 시민/마피아 슈퍼바이저 모두 첫 번째 AI 플레이어를 고정 타겟으로 지정. trust_score 미활용.

**목표**: trust_score 기반 동적 전략 수립.

**구체적 작업**:

시민 슈퍼바이저 (`supervisors/citizen.py`):
```python
# 의심 대상 = trust_score 가장 낮은 플레이어
suspect = min(alive_ai_players, key=lambda p: p.trust_score)

# 경찰 조사 결과가 reports에 있으면 우선 반영
for r in reports:
    if "mafia" in r.content.lower():
        # 마피아 확인된 플레이어를 최우선 타겟으로
        ...
```

마피아 슈퍼바이저 (`supervisors/mafia.py`):
```python
# AGENT_DESIGN.md 우선순위 구현
# 1순위: 경찰 역할 (role=detective) 플레이어
# 2순위: 의사 역할 (role=doctor) 플레이어  
# 3순위: trust_score 높은 시민 (영향력 높음)
# 4순위: 무작위 시민
```

**참조 문서**: `AGENT_DESIGN.md` §3.2, §3.3

---

## 🟡 중간 우선순위 작업

### [C-4] 마피아 밤 채팅 채널 분리

**현황**: `mafia_secret` 채널이 코드에 정의는 됐으나 실제 분리 로직 없음. 밤에 마피아끼리 협의하는 채널이 프론트에 노출되지 않음.

**목표**: 밤 Phase에서 마피아만 볼 수 있는 채널 분리.

**구체적 작업**:
```
1. websocket/manager.py: 채널별 broadcast 필터링
   - mafia_secret 채널은 마피아 팀 플레이어에게만 전송
   - spy_listen 채널은 스파이에게도 전송 (미러)
2. graph.py: 마피아 Agent 발언 채널을 night_mafia Phase에서 mafia_secret으로 설정
3. runner.py: NIGHT_MAFIA Phase에서 마피아 협의 채팅 처리
```

**참조 문서**: `TECH_ARCHITECTURE.md` §3.2 채팅 채널 분리

---

### [C-5] Redis Checkpointer 연동

**현황**: LangGraph Checkpointer 없음. Agent가 라운드 간 이전 관찰 내용을 기억하지 못함.

**목표**: thread_id = `{game_id}_{agent_id}` 기준으로 Agent별 상태 영속화.

**구체적 작업**:
```python
from langgraph.checkpoint.redis import RedisSaver
import redis

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
checkpointer = RedisSaver(redis_client)

# AgentGraph 내 컴파일 시 checkpointer 주입
self._agent_call_graph = day_chat_graph.compile(checkpointer=checkpointer)

# 각 Agent 호출 시 config 전달
config = {"configurable": {"thread_id": f"{game_id}_{agent_id}"}}
await self._agent_call_graph.ainvoke(state, config=config)
```

**참조 문서**: `RAG_AND_STORAGE_DESIGN.md` §4 Redis 키 설계

---

### [C-6] 발언 타이밍 랜덤 딜레이 추가

**현황**: Agent들이 동시에 순차 실행되어 자연스럽지 않은 발언 패턴.

**목표**: Agent 성격(verbosity, aggression)에 따른 발언 타이밍 제어.

**구체적 작업**:
```python
# graph.py run_day_chat_round() 내부
for agent_id, agent in self.agents.items():
    # 성격 기반 딜레이 (0.5 ~ 15초)
    verbosity = agent.persona.verbosity  # 0.0(과묵) ~ 1.0(수다)
    base_delay = 15 * (1 - verbosity)    # 과묵할수록 늦게 발언
    jitter = random.uniform(0, 3)
    await asyncio.sleep(base_delay + jitter)
    
    # 이후 agent.run() 호출
```

---

### [C-7] game/roles.py 능력 로직 구현

**현황**: detective/doctor/mafia/killer 함수가 시그니처만 있고 실제 로직 없음.

**목표**: 밤 능력 결과가 GameState에 실제로 반영되어야 함.

**구체적 작업**:
```python
def detective_investigate(ctx: RoleAbilityContext) -> GameState:
    # 대상의 team(mafia 여부) 확인 → 경찰 Agent의 메모리에 기록
    if ctx.target:
        result = f"{ctx.target.name}은 {ctx.target.team.value}입니다."
        # ctx.actor의 observation 메모리에 추가
    return ctx.game_state

def doctor_protect(ctx: RoleAbilityContext) -> GameState:
    # 대상 Player에 protected=True 플래그 추가 (임시)
    # 마피아 공격 시 protected 체크해서 무효화
    return ctx.game_state

def mafia_attack(ctx: RoleAbilityContext) -> GameState:
    # doctor가 보호 중이 아니면 is_alive = False
    # player_death 이벤트 GameState.events에 추가
    return ctx.game_state
```

---

## ✅ 완료 보고 형식

작업 완료 후 Claude에게 아래 형식으로 보고:

```
[완료] C-N — 작업명

구현 내용:
- ...

설계와 다르게 구현한 부분 (있을 경우):
- ...

다음 작업 전 확인 필요 사항:
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
