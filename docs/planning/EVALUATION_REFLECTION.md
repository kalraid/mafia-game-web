# 평가 피드백 반영 설계서 (EVALUATION_REFLECTION)

> **문서 버전**: v1.0  
> **작성일**: 2026-03-18  
> **목적**: 이전 프로젝트 평가 피드백 분석 → 현재 프로젝트 설계 반영

---

## 1. 평가에서 도출된 핵심 평가 요소

이전 평가 피드백을 분석한 결과, 평가자가 보는 핵심 기준은 다음 6가지입니다.

| # | 평가 요소 | 핵심 질문 |
|---|----------|----------|
| 1 | **진짜 에이전트인가** | 함수 파이프라인인가? 자율 판단 루프인가? |
| 2 | **Tool Calling 자율성** | LLM이 도구를 스스로 선택하는가? |
| 3 | **메모리/멀티턴** | 대화 이력이 LLM 호출에 실제로 전달되는가? |
| 4 | **RAG 실질성** | 샘플 데이터인가? 실제 검색이 결과에 영향 주는가? |
| 5 | **출력 스키마 일관성** | 전 노드에 Structured Output이 적용됐는가? |
| 6 | **문서-구현 정합성** | 설계 문서와 실제 코드가 일치하는가? |

---

## 2. 평가 요소별 상세 분석 및 현재 프로젝트 반영

---

### 평가 요소 1: 진짜 에이전트인가 (Agent vs Pipeline)

**피드백 원문**
> 멀티 에이전트가 '협업하는 에이전트'라기보다는 '단계별 함수 파이프라인'에 가까워 보여서,
> 감독(Planner)이 정보의 갭을 진단하고 재검색/재질문/검증을 지시하는 루프를 추가하면
> 에이전트성이 크게 강화됩니다.

**무엇이 문제인가**
- 노드 A → 노드 B → 노드 C 순서가 고정된 것은 파이프라인
- 진짜 에이전트는 상황에 따라 분기, 재시도, 루프백이 발생해야 함

**현재 프로젝트 반영 설계**

```
✅ 슈퍼바이저가 매 Phase마다 상황을 진단하고 지시를 동적으로 생성
✅ Agent가 발언 후 슈퍼바이저가 품질 검증 → 재생성 요청 가능
✅ 투표 결과를 보고 다음 전략을 재수립하는 피드백 루프 존재
✅ 마피아 슈퍼바이저: 경찰이 의심되면 우선 제거 대상을 동적 변경
✅ 시민 슈퍼바이저: 라운드별 trust_score 재계산 후 의심 대상 재지정

구체적 루프 설계:
  낮 채팅 Phase 종료
    → 슈퍼바이저: 이번 라운드 발언 분석
    → 정보 갭 발견 시 (경찰이 조사 안 함, 의사가 침묵)
    → 다음 밤 전 directive 재발행
    → Agent: directive 읽고 행동 조정
```

**반영 위치**: `AGENT_DESIGN.md` → 슈퍼바이저 설계, LangGraph 구조

---

### 평가 요소 2: Tool Calling 자율성

**피드백 원문**
> Tool calling이 LLM의 자율 선택이 아니라 노드 내부에서 수동 실행되는 형태라,
> LangGraph의 ToolNode + tool binding으로 "필요 시 DB조회/웹검색/OCR/파싱"을
> 선택하도록 바꾸면 설계 의도가 더 선명해집니다.

**무엇이 문제인가**
- 코드에서 직접 `search_db()` 호출하는 것 = 수동 실행
- LLM이 "지금 DB 조회가 필요하다"고 판단해서 Tool을 선택해야 함

**현재 프로젝트 반영 설계**

```python
# ❌ 나쁜 예 (수동 실행, 파이프라인)
def agent_node(state):
    rag_result = search_rag(state["situation"])   # 항상 실행
    directive = get_directive(state["agent_id"])  # 항상 실행
    response = llm.invoke(prompt)
    return response

# ✅ 좋은 예 (LLM이 Tool 자율 선택)
tools = [
    get_game_state_tool,      # 게임 상태 조회
    get_chat_history_tool,    # 채팅 히스토리 조회
    search_strategy_rag_tool, # 전략 RAG 검색
    get_directive_tool,       # 슈퍼바이저 지시 조회
    send_chat_tool,           # 채팅 발언
    submit_vote_tool,         # 투표 제출
    use_ability_tool,         # 능력 사용
    report_to_supervisor_tool # 슈퍼바이저 보고
]

agent = llm.bind_tools(tools)
# LLM이 필요한 Tool을 스스로 판단해서 호출
```

```
LangGraph ToolNode 연동:
  agent_node → (tool_calls 있으면) → ToolNode → agent_node (재실행)
  이 루프가 Tool 호출이 없을 때까지 반복
  → 진짜 ReAct 에이전트 패턴
```

**반영 위치**: `AGENT_DESIGN.md` → MCP Tool 설계, Agent Node 구조
**Cursor 지시**: Agent Node 구현 시 반드시 `bind_tools` + `ToolNode` 패턴 사용

---

### 평가 요소 3: 메모리 / 멀티턴

**피드백 원문**
> 메모리는 UI에 chat_history가 존재하지만 LLM 호출에 메시지가 전달되지 않아
> 멀티턴 상담으로 확장되지 못했습니다. LangGraph checkpointer(SQLite 등) 또는
> store를 붙여 상태/대화 이력을 누적 전달하면 상담형 UX의 강점이 살아납니다.

**무엇이 문제인가**
- UI에 채팅이 쌓여 보여도, LLM 호출 시 messages=[] 로 보내면 의미 없음
- Agent가 이전 라운드를 "기억"해야 전략적 행동이 가능

**현재 프로젝트 반영 설계**

```
메모리 계층 (3단계):

1. LangGraph Checkpointer (Redis)
   → Agent의 LangGraph 실행 상태 전체 저장
   → thread_id = f"{game_id}_{agent_id}"
   → 다음 Phase 실행 시 이전 상태 이어받음

2. Agent 개인 메모리 (Redis key: agent:{game_id}:{id}:memory)
   → 이번 게임에서 관찰한 정보 누적
   예: {
     "suspected": ["player_3", "player_7"],
     "trusted": ["player_2"],
     "known_mafia": [],        # 경찰만 가짐
     "observations": [
       "라운드1: player_3이 너무 빠르게 player_5를 지목함",
       "라운드2: player_7이 마피아 채팅 패턴과 유사한 발언"
     ]
   }

3. LLM 호출 시 messages 구성
   → system: 역할/페르소나 + 현재 게임 상황
   → 이전 발언들: Agent의 관찰 메모리 요약
   → human: 현재 Phase 지시
   → 채팅 히스토리: 최근 10개 메시지 (컨텍스트 윈도우 관리)
```

**반영 위치**: `RAG_AND_STORAGE_DESIGN.md`, `AGENT_DESIGN.md`
**Cursor 지시**: LangGraph 구현 시 반드시 Redis Checkpointer 연동, messages에 history 포함

---

### 평가 요소 4: RAG 실질성

**피드백 원문**
> 내부 KB가 샘플 수준(2건)이라 설계 대비 효과가 약했습니다.
> 실제 공공데이터 수집·정제·정규화 파이프라인과 메타데이터를 포함한 인덱싱으로
> "내부DB 우선" 전략이 설득력을 얻을 수 있습니다.

**무엇이 문제인가**
- RAG가 있어도 문서 2~3개면 검색 결과가 무의미함
- 메타데이터 없이 저장하면 필터링/정밀 검색 불가

**현재 프로젝트 반영 설계**

```
RAG 지식베이스 목표 규모:
  - 전략 문서: 카테고리당 최소 10개 이상의 실질적 문서
  - 발언 패턴: 역할별 50개+ 예시 문장
  - 상황별 사례: 인원 구성×라운드 조합으로 30개+ 시나리오

메타데이터 설계 (검색 필터링용):
  {
    "category": "strategy",          # strategy|speech|situation|rule
    "role": "mafia",                  # 적용 역할
    "team": "mafia",                  # 진영
    "game_size": "medium",            # small(4-7)|medium(8-12)|large(13-20)
    "round_phase": "mid",             # early|mid|end
    "speech_style": "aggressive",     # 발언 패턴 카테고리
    "source": "static"                 # static|runtime
  }

RAG 검색 고도화:
  1. 메타데이터 필터 선적용 (역할, 게임 규모)
  2. 의미 유사도 검색 (Top-K=5)
  3. MMR(Maximal Marginal Relevance)으로 다양성 확보
  4. 검색 결과를 프롬프트에 "전략 참고자료"로 명시 주입

RAG 효과 검증 포인트 (Cursor가 구현 시 필수):
  - 검색된 문서 제목/스니펫을 Agent 내부 로그에 기록
  - 검색 결과 없을 때 fallback 처리 (기본 전략 프롬프트 사용)
  - state에 rag_context 키로 보존 → 디버깅 가능하게
```

**반영 위치**: `RAG_AND_STORAGE_DESIGN.md`
**Cursor 지시**: ChromaDB 문서 삽입 시 메타데이터 반드시 포함, 최소 문서 수 확보

---

### 평가 요소 5: 출력 스키마 일관성 (Structured Output)

**피드백 원문**
> 출력 구조가 노드별로 혼재(일부 substring 기반 파싱, 상태 키 불일치)하여
> 실행 안정성을 해칠 수 있어, 전 노드에 스키마(필드명/타입) 통일 +
> Structured Output 강제(일관 파서, 실패 시 재시도)를 적용하면 견고해집니다.

**무엇이 문제인가**
- 노드마다 출력 형식이 다르면 다음 노드에서 KeyError 발생
- `response.split(":")` 같은 파싱은 LLM 출력 조금만 바뀌어도 실패

**현재 프로젝트 반영 설계**

```python
# 전체 Agent 출력 스키마 통일

class AgentSpeechOutput(BaseModel):
    speech: Optional[str]        # 채팅 발언 내용 (없으면 None)
    reasoning: str               # 내부 추론 (디버그용)
    confidence: float            # 0.0~1.0

class AgentVoteOutput(BaseModel):
    target_id: str               # 투표 대상 player_id
    reasoning: str               # 투표 이유

class AgentAbilityOutput(BaseModel):
    ability: str                 # "investigate"|"heal"|"attack"
    target_id: str               # 능력 대상
    reasoning: str

class SupervisorDirective(BaseModel):
    target_agent: str
    strategy_type: str           # "speech"|"vote"|"ability"
    instruction: str
    priority: Literal["high", "medium", "low"]

# LLM 호출 시 with_structured_output 사용
structured_llm = llm.with_structured_output(AgentSpeechOutput)
result = structured_llm.invoke(messages)
# → 파싱 실패 시 자동 재시도 (max_retries=2)
```

```
추가 안전장치:
  - 모든 Agent 노드에 try/except + 재시도 로직
  - 파싱 실패 3회 시 기본값(침묵/랜덤 투표) fallback
  - 실패 원인 logging (except: pass 절대 금지)
  - state 키 이름을 models/에서 상수로 관리
```

**반영 위치**: `TECH_ARCHITECTURE.md` → 데이터 모델 섹션
**Cursor 지시**: `with_structured_output` 전 노드 적용, `except: pass` 금지, 상수 키 관리

---

### 평가 요소 6: 문서-구현 정합성

**피드백 원문**
> 기술 스택 설명에서 계획(FastAPI, 구조화 파서 등)과 구현이 일부 불일치한 부분이 있어,
> 문서에 "현재 구현 범위/미구현 항목/추후 로드맵"을 분리해 적으면
> 설계 이해도와 전달력이 더 좋아집니다.

**무엇이 문제인가**
- 문서에 FastAPI라고 써놓고 Streamlit 단독으로 구현하면 감점
- "계획했지만 못 한 것"을 숨기면 더 안 좋음 — 솔직하게 분리해야 함

**현재 프로젝트 반영 설계**

```
TASK_PLAN.md에 구현 상태 컬럼 추가:
  | 태스크 | 상태 | 비고 |
  |--------|------|------|
  | FastAPI WebSocket | ✅ 구현 | |
  | Redis Checkpointer | 🔄 진행중 | |
  | RAG 지식베이스 | ⬜ 미구현 | Phase 5 예정 |

PRD.md에 구현 범위 섹션 추가:
  - MVP 범위 (반드시 구현)
  - 2단계 범위 (시간 허용 시)
  - 로드맵 (추후)
```

**반영 위치**: `TASK_PLAN.md` 상태 컬럼 추가, `PRD.md` 구현 범위 명시

---

## 3. 반영 체크리스트 (Cursor/Gemini 구현 시 필수 확인)

### 백엔드 (Cursor)
- [ ] Agent Node: `bind_tools` + `ToolNode` 패턴 (수동 Tool 호출 금지)
- [ ] Agent Node: `with_structured_output` 전 노드 적용
- [ ] LangGraph: Redis Checkpointer 연동 (thread_id = game_id + agent_id)
- [ ] LLM 호출: messages에 chat_history 누적 전달
- [ ] 슈퍼바이저: 매 Phase 상황 진단 → 재지시 루프
- [ ] RAG: 메타데이터 포함 문서 삽입, 최소 규모 확보
- [ ] 예외 처리: `except: pass` 금지, 로깅 + fallback 필수
- [ ] 상태 키: `models/`에서 상수 관리, 노드 간 키 일관성

### 프론트엔드 (Gemini)
- [ ] 구현된 기능만 UI에 표시 (미구현 기능 버튼 비활성 처리)
- [ ] WebSocket 연결 실패 시 에러 UI 표시
- [ ] 로딩 상태 표시 (AI 발언 생성 중 스피너)

---

## 4. 추가 강화 포인트 (보너스)

피드백에서 언급하지 않았지만 현재 설계에서 선제적으로 강화한 부분:

| 항목 | 내용 |
|------|------|
| A2A 통신 | 슈퍼바이저↔Agent 지시 체계 명확화 (단순 파이프라인 방지) |
| 페르소나 일관성 | Agent가 게임 내내 같은 말투/성격 유지 (checkpointer 활용) |
| 발언 타이밍 제어 | 랜덤 딜레이로 자연스러운 대화 흐름 |
| 마피아 협의 채널 | 밤에 마피아끼리 실제로 협의하는 채팅 채널 분리 |
| 게임 결과 저장 | Redis에 이벤트 로그 보존 → 게임 리뷰 가능 |
