# ⚙️ Cursor 작업 지시서 (WORK_ORDER_CURSOR)

> **대상**: Cursor AI — 백엔드 개발자  
> **작성자**: Claude AI (기획자 + 인프라)  
> **최종 업데이트**: 2026-03-19 (b6d9fe1 반영)

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
| — | NIGHT_MAFIA 라운드 + mafia_secret 채널 | `af1a977` |
| — | Phase 가드 (허용 행동만 반환) | `af1a977` |
| — | `_AgentCallState` 직렬화 개선 (`_invoke_agent()` 헬퍼) | `b6d9fe1` |
| — | `langgraph-checkpoint-redis` requirements 추가 | `b6d9fe1` |
| — | `backend/Dockerfile` 경로 이동 (루트→backend/) | `b6d9fe1` |

---

## 🔄 진행 중 작업

### [C-2] MCP bind_tools + ToolNode 연동 — 다음 단계

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

**참조**: `AGENT_DESIGN.md` §2.2, `EVALUATION_REFLECTION.md` §평가요소2

---

### [C-5] Redis Checkpointer 전면 연동

**현황**: `MAFIA_USE_REDIS_CHECKPOINTER=1`일 때만 RedisSaver 사용, 실패 시 일반 compile 폴백.  
docker-compose에 `MAFIA_USE_REDIS_CHECKPOINTER=1` 설정되어 있으음 (Claude 처리).

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

## 🟡 중간 우선순위 작업

### [C-7] game/roles.py 능력 로직 구현

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
