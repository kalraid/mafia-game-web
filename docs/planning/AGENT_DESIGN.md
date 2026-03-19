# AI Agent 설계 명세서 (AGENT_DESIGN)

> **문서 버전**: v1.1  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-18  
> **변경 내용**: Agent Node를 bind_tools + ToolNode 패턴으로 변경 (파이프라인 방지)

---

## 1. Agent 시스템 전체 구조

```
┌───────────────────────────────────────────────────────────────┐
│                    Game Engine                                 │
│               (Phase / Timer / Event)                         │
└──────────────────────────┬────────────────────────────────────┘
                           │ 이벤트 발생
          ┌────────────────▼─────────────────┐
          │       LangGraph Main Graph        │
          │    (게임 전체 흐름 오케스트레이션)  │
          └───┬──────────────┬───────────────┘
              │              │
   ┌──────────▼──┐     ┌─────▼──────────────────────────┐
   │  메인       │     │      슈퍼바이저 레이어           │
   │  슈퍼바이저 │     │                                  │
   │  (진행 판단)│     │  ┌──────────┐ ┌──────────┐     │
   └─────────────┘     │  │ 시민     │ │ 마피아   │     │
                        │  │ 슈퍼바이저│ │ 슈퍼바이저│    │
                        │  └────┬─────┘ └────┬─────┘    │
                        │       │             │           │
                        │  ┌────▼─────┐  ┌───▼──────┐  │
                        │  │ 중립     │  │ A2A 지시 │  │
                        │  │ 슈퍼바이저│  │ 채널     │  │
                        │  └──────────┘  └──────────┘  │
                        └─────────────────────────────────┘
                                      │
                    ┌─────────────────▼──────────────────────┐
                    │           Agent Pool                     │
                    │  Agent_1(경찰)  Agent_2(시민) ...       │
                    │  Agent_5(마피아) Agent_6(의사) ...      │
                    │     (각각 ReAct 패턴 LangGraph Node)    │
                    └─────────────────────────────────────────┘
```

---

## 2. LangGraph 구성

### 2.1 Main Graph (게임 오케스트레이터)

```
Node: phase_router
  → 현재 Phase를 보고 다음 실행할 서브그래프 결정

SubGraph: day_chat_graph
  → 낮 채팅 Phase: 각 Agent 순서대로 발언 생성
  → Phase 종료 후 슈퍼바이저 재진단 루프 실행

SubGraph: vote_graph
  → 투표 Phase: 각 Agent가 투표 대상 결정

SubGraph: night_graph
  → 밤 Phase: 마피아 협의 → 능력 사용 → 결과 계산

Node: supervisor_replan
  → 각 Phase 종료 후 슈퍼바이저가 상황 재진단
  → 정보 갭 발견 시 directive 재발행 (진짜 에이전트 루프)

Node: win_condition_checker
  → 각 Phase 종료 후 승리 조건 확인
```

### 2.2 Agent Node 구조 — ReAct 패턴 (bind_tools + ToolNode)

> ⚠️ **중요**: Agent는 수동으로 Tool을 호출하지 않습니다.
> LLM이 필요한 Tool을 스스로 판단하여 호출하는 ReAct 패턴을 사용합니다.

```python
# ✅ 올바른 구현 패턴
tools = [
    get_game_state_tool,        # 게임 상태 조회
    get_chat_history_tool,      # 채팅 히스토리 조회
    search_strategy_rag_tool,   # 전략 RAG 검색
    get_directive_tool,         # 슈퍼바이저 지시 조회
    get_my_memory_tool,         # 내 관찰 메모리 조회
    send_chat_tool,             # 채팅 발언
    submit_vote_tool,           # 투표 제출
    use_ability_tool,           # 능력 사용
    report_to_supervisor_tool,  # 슈퍼바이저 보고
]

# LLM에 Tool 바인딩
agent_llm = llm.bind_tools(tools)

# LangGraph 노드
def agent_node(state: GameState) -> GameState:
    messages = build_messages(state)   # 시스템 프롬프트 + 히스토리 구성
    response = agent_llm.invoke(messages)
    return {"messages": [response]}

# Tool 실행 노드
tool_node = ToolNode(tools)

# 그래프 연결: agent → (tool_calls 있으면) → tool_node → agent (반복)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_conditional_edges(
    "agent",
    should_continue,   # tool_calls 있으면 tools로, 없으면 종료
)
graph.add_edge("tools", "agent")
```

```
# ❌ 금지 패턴 (수동 파이프라인)
def agent_node(state):
    rag_result = search_rag(state)      # 항상 실행 → 파이프라인
    directive = get_directive(state)    # 항상 실행 → 파이프라인
    response = llm.invoke(prompt)
    return response
```

---

## 3. 슈퍼바이저 (Supervisor) 설계

### 3.1 슈퍼바이저 재진단 루프 (핵심)

슈퍼바이저는 단순히 지시만 내리는 것이 아니라, **매 Phase 종료 후 상황을 재진단**하고 필요 시 전략을 수정합니다.

```
[낮 채팅 Phase 종료]
        ↓
[슈퍼바이저 재진단]
  - 이번 라운드 발언 패턴 분석
  - 정보 갭 확인 (경찰 조사 안 함? 의사 침묵?)
  - trust_score 재계산
        ↓
[전략 수정 필요?]
  YES → 새 directive 발행 → Agent들이 다음 행동에 반영
  NO  → 기존 전략 유지
        ↓
[다음 Phase 진입]
```

### 3.2 시민 슈퍼바이저

**매 낮 Phase 수행**:
1. 의심 대상 목록 업데이트 (trust_score 기반)
2. 각 시민 Agent에게 발언 전략 지시 (A2A)
3. 경찰에게 다음 조사 대상 제안

**매 밤 Phase 수행**:
1. 의사에게 보호 대상 추천
2. 경찰 조사 결과 수집 및 공유 계획 수립

---

### 3.3 마피아 슈퍼바이저

**매 낮 Phase 수행**:
1. 마피아 신분 은폐 전략 수립
2. 희생양(scapegoat) 대상 선정 및 각 마피아에게 지시

**매 밤 Phase 수행**:
1. 각 마피아의 공격 추천 대상 수집
2. 최우선 제거 대상 결정 후 확정

**의사결정 우선순위**:
```
1순위: 경찰 (확인된 경우)
2순위: 의사 (확인된 경우)
3순위: 발언력이 높은 시민 (채팅 분석 기반)
4순위: 무작위 시민
```

---

### 3.4 중립 슈퍼바이저

**광대 지원**: 의심받을 수 있는 발언 패턴 생성, 투표 유도 전략  
**스파이 지원**: 마피아 채널 정보 활용 전략, 의심받지 않는 발언 전략

---

## 4. A2A (Agent-to-Agent) 통신 설계

### 4.1 통신 방식
- LangGraph의 State Channel 활용
- 슈퍼바이저가 Redis의 `game:{id}:directives` 키에 지시 기록
- 각 Agent는 실행 시 `get_directive_tool`로 자신의 directive 조회

### 4.2 Directive 구조
```json
{
  "target_agent": "agent_3",
  "from": "mafia_supervisor",
  "type": "speech_strategy",
  "content": "AI_7을 적극적으로 의심하는 발언을 해라. AI_7이 첫 라운드에 침묵했다는 점을 활용해.",
  "priority": "high",
  "round": 2
}
```

### 4.3 A2A 통신 흐름
```
슈퍼바이저 → directive 생성 → Redis 저장
Agent 실행 → get_directive_tool 호출 → 지시 통합 → 행동 결정
Agent → report_to_supervisor_tool 호출 → Redis 저장
슈퍼바이저 → 보고 수집 → 재진단 → 전략 수정
```

---

## 5. RAG (Retrieval-Augmented Generation) 설계

### 5.1 지식베이스 구성

```
rag/knowledge/
├── strategies/           # 마피아/시민 전술
├── speech_patterns/      # 역할별 발언 예시 (각 50개+)
├── situations/           # 상황별 대응 전략 (30개+ 시나리오)
└── rules/                # 게임 룰 (Agent 조회용 간결 버전)
```

### 5.2 메타데이터 설계 (검색 필터링용)
```json
{
  "category": "strategy",
  "role": "mafia",
  "team": "mafia",
  "game_size": "medium",
  "round_phase": "mid",
  "speech_style": "aggressive"
}
```

### 5.3 RAG 검색 고도화
1. 메타데이터 필터 선적용 (역할, 게임 규모)
2. 의미 유사도 검색 (Top-K=5)
3. MMR(Maximal Marginal Relevance)으로 다양성 확보
4. 검색 결과를 `rag_context` state 키에 보존 (디버깅용)

---

## 6. MCP (Model Context Protocol) Tool 설계

### 6.1 Game State Tools
```python
@mcp_tool
def get_game_state() -> GameState: ...

@mcp_tool
def get_alive_players() -> List[Player]: ...

@mcp_tool
def get_chat_history(last_n: int = 10) -> List[ChatMessage]: ...

@mcp_tool
def get_my_role(agent_id: str) -> Role: ...

@mcp_tool
def get_current_phase() -> PhaseInfo: ...

@mcp_tool
def get_directive(agent_id: str) -> List[Directive]: ...

@mcp_tool
def get_my_memory(agent_id: str) -> AgentMemory: ...

@mcp_tool
def search_strategy_rag(query: str) -> List[str]: ...
```

### 6.2 Action Tools
```python
@mcp_tool
def send_chat(agent_id: str, content: str, channel: str = "global") -> bool: ...

@mcp_tool
def submit_vote(agent_id: str, target_id: str) -> bool: ...

@mcp_tool
def use_ability(agent_id: str, ability: str, target_id: str) -> AbilityResult: ...

@mcp_tool
def report_to_supervisor(agent_id: str, report: str) -> bool: ...
```

### 6.3 Supervisor-Only Tools
```python
@mcp_tool
def issue_directive(supervisor_id: str, target_agent: str, directive: Directive) -> bool: ...

@mcp_tool
def get_all_reports(supervisor_id: str) -> List[Report]: ...

@mcp_tool
def analyze_trust_scores() -> Dict[str, float]: ...
```

---

## 7. Structured Output (출력 스키마 통일)

> ⚠️ **전 노드 필수 적용**: `with_structured_output` 사용, `except: pass` 금지

```python
class AgentSpeechOutput(BaseModel):
    speech: Optional[str]
    reasoning: str           # 내부 추론 (디버그용)
    confidence: float        # 0.0~1.0

class AgentVoteOutput(BaseModel):
    target_id: str
    reasoning: str

class AgentAbilityOutput(BaseModel):
    ability: str             # "investigate"|"heal"|"attack"
    target_id: str
    reasoning: str

class SupervisorDirective(BaseModel):
    target_agent: str
    strategy_type: str
    instruction: str
    priority: Literal["high", "medium", "low"]

# 사용 예시
structured_llm = llm.with_structured_output(AgentSpeechOutput)
# 파싱 실패 시 max_retries=2 자동 재시도
```

---

## 8. Agent 메모리 구조 (Redis)

```python
# 게임 내 Agent 개인 관찰 메모리
agent_memory = {
    "suspected": ["player_3", "player_7"],   # 의심 목록
    "trusted": ["player_2"],                  # 신뢰 목록
    "known_mafia": [],                        # 확인된 마피아 (경찰만)
    "observations": [
        "라운드1: player_3이 너무 빠르게 player_5를 지목함",
        "라운드2: player_7이 마피아 채팅 패턴과 유사한 발언"
    ]
}
# Redis key: agent:{game_id}:{agent_id}:memory
```

---

## 9. Agent 페르소나 설계

```python
class AgentPersona(BaseModel):
    name: str              # 한국 이름
    speech_style: str      # "격식체"|"반말"|"조심스러운"|"공격적"
    aggression: float      # 0.0~1.0
    trust_tendency: float  # 0.0~1.0
    verbosity: float       # 0.0~1.0
    logic_style: str       # "감정형"|"논리형"|"직관형"
```

---

## 10. Agent 실행 동시성

- **낮 Phase**: asyncio gather로 동시 추론, 랜덤 순서 + 딜레이로 순차 출력
- **밤 Phase**: 역할별 병렬 실행 → 결과 집계
- **Redis Checkpointer**: `thread_id = f"{game_id}_{agent_id}"` 로 Agent별 독립 상태 유지
