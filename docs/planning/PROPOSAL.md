# **AI Mafia Online — 박찬호**

> AI Bootcamp 최종 과제 제출 기획서  
> 제출일: 2026-04-06

---

## **1. 프로젝트 개요 – 기획 배경 및 핵심 내용**

### **1.1 프로젝트 기획 배경**

**해결하고자 하는 문제**

마피아 게임은 심리전과 추리를 결합한 고도의 사회적 게임이지만, 현실에서는 항상 같은 문제가 반복됩니다. "사람을 못 모은다." 최소 6명이 필요한 게임 특성상, 퇴근 후나 새벽에 즉흥적으로 하고 싶어도 인원 수급이 불가능합니다.

**기존 방식의 한계**

- 온라인 마피아 플랫폼: 낯선 사람과의 매칭 대기(평균 5~15분), 비매너 유저 조기 이탈 문제
- 기존 AI 챗봇: 단순 Q&A 형태로 "역할에 맞는 전략적 판단"과 "다른 AI와의 실시간 심리전"이 불가능
- 싱글플레이 보드게임 AI: 정해진 규칙 기반 봇 수준으로 예측이 너무 쉬워 흥미 반감

**Agent 서비스로 해결할 수 있는 Pain Point**

| Pain Point | AI Mafia Online 해결 방식 |
|-----------|------------------------|
| 인원 부족 | AI 플레이어가 빈 자리를 채움 — 즉시 게임 시작 |
| 단순한 AI 행동 | 팀별 Supervisor가 AI에게 전략 지시 → 역할별 페르소나 기반 자율 판단 |
| 게임 반복 시 패턴 고정 | 게임 종료 후 승리 패턴을 RAG에 자동 학습 → 매 판 다른 전술 |
| 몰입감 부족 | 발언 타이밍 딜레이, 페르소나 기반 말투 차이로 실제 플레이어처럼 표현 |

**프로젝트 시작 동기**

LangGraph의 멀티 에이전트 구조를 학습하면서 "여러 AI가 서로 다른 역할을 맡고 서로를 속이며 협력하는 구조"가 마피아 게임과 완벽히 일치한다는 점에서 착안했습니다. 단순 데모를 넘어, 실제로 사람이 AI와 함께 즐길 수 있는 완결형 서비스로 구현하는 것을 목표로 설정했습니다.

---

### **1.2 핵심 아이디어 및 가치 제안 (Value Proposition)**

**서비스 핵심 기능**

1. **즉시 게임 시작**: 혼자 접속해도 AI가 나머지 자리를 채워 6~8인 게임 즉시 진행
2. **역할 기반 자율 AI**: 마피아·경찰·의사·시민·중립 역할을 맡은 AI가 각자의 목표에 따라 전략적으로 발언·투표·능력 사용
3. **팀 전략 지휘 체계**: CitizenSupervisor / MafiaSupervisor / NeutralSupervisor가 팀 상황을 분석하고 소속 AI들에게 실시간 지시문 발행
4. **자기학습 RAG**: 게임 종료 후 GameInsightAgent가 승리 패턴을 자동 추출해 지식베이스에 추가 → 다음 게임에서 더 정교한 전략 활용

**사용자에게 제공되는 가치**

- "언제든, 혼자서도" 마피아 게임 가능
- 매 판마다 다른 AI 전술로 반복 플레이에도 신선한 경험
- AI의 내부 추론 과정(internal_notes)을 통해 AI가 왜 그런 판단을 했는지 관전 가능

**기존 서비스 대비 차별성**

| 구분 | 기존 온라인 마피아 | AI Mafia Online |
|-----|----------------|----------------|
| 인원 요건 | 최소 6명 대기 필요 | 1명부터 즉시 시작 |
| AI 수준 | 없거나 단순 봇 | LangGraph 멀티 에이전트, 전략적 심리전 |
| 학습 능력 | 없음 | 게임 결과 자동 RAG 학습 |
| 팀 전략 | 없음 | Supervisor → Agent 지시 체계 |

---

### **1.3 대상 사용자 및 기대 사용자 경험 (UX)**

**주요 타겟**

- **일반 게임 사용자**: 마피아를 좋아하지만 인원 모으기 어려운 20~35세
- **AI 기술 학습자**: AI 에이전트가 역할극하며 추론하는 과정을 직접 관찰하고 싶은 개발자/학생

**사용자 경험 흐름**

```
① 접속 → 게임 생성(인원 설정) → 역할 배정
② 낮 단계: 채팅창에서 AI들의 발언 실시간 확인, 의심 발언 직접 참여
③ 투표 단계: 처형 대상 투표 (AI와 동일 권한)
④ 밤 단계: 역할에 따라 능력 사용 (경찰: 조사, 의사: 보호, 마피아: 공격)
⑤ 게임 종료: 승리팀 발표, AI 신뢰도 점수 시각화, 내부 추론 로그 공개
```

**구체적 Benefit**

- 대기 없이 즉시 시작하는 몰입감
- AI의 발언이 단순 랜덤이 아닌, trust_score 기반 표적 지정·팀 전략 반영으로 사람처럼 느껴지는 경험
- 관전자도 AI 내부 추론(reasoning, confidence score)을 통해 AI의 판단 근거 학습 가능

---

## **2. 기술 구성 – 서비스에 적용한 기술 스택**

### **2.1 Prompt Engineering 전략**

**역할 기반 프롬프트**

각 AI 플레이어는 게임 시작 시 고유한 페르소나(AgentPersona)를 부여받습니다.

```
- speech_style: 격식체 / 반말 / 조심스러운 / 공격적
- aggression: 0.0 ~ 1.0 (얼마나 적극적으로 의심하는가)
- trust_tendency: 0.0 ~ 1.0 (타인을 쉽게 믿는가)
- logic_style: 감정형 / 논리형 / 직관형
```

**CoT (Chain-of-Thought) 설계**

LLM이 발언·투표를 결정할 때 내부 추론(`reasoning`)을 먼저 생성한 뒤 최종 결정을 출력하는 2단계 구조:

```
[1단계] 현재 게임 상태 분석 (생존자, 투표 패턴, RAG 전략 참조)
[2단계] Supervisor 지시문 + 페르소나 기반 최종 행동 결정 → AgentDecision 출력
```

**Structured Output 템플릿**

`with_structured_output(AgentDecision)` 으로 LLM 응답을 강제 구조화:

```python
class AgentDecision(BaseModel):
    speech: Optional[str]          # 발언 내용
    vote_target: Optional[str]     # 투표 대상
    ability: Optional[str]         # 능력명
    ability_target: Optional[str]  # 능력 대상
    reasoning: str                 # 내부 추론 (CoT)
    confidence: float              # 0.0~1.0 확신도
```

**상황별 프롬프트 분기**

Phase(낮 채팅 / 낮 투표 / 밤 마피아 / 밤 능력)마다 `phase_instruction`이 달라지며, 허용 출력 필드도 Phase별로 필터링됩니다. 예를 들어 DAY_CHAT에서는 `speech`만, DAY_VOTE에서는 `vote_target`만 반영합니다.

---

### **2.2 LangChain / LangGraph 기반 Agent 구조**

**Multi-Agent 설계 개념**

```
[GameRunner] ── Phase 루프 ──▶ [AgentGraph]
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
        CitizenSupervisor   MafiaSupervisor   NeutralSupervisor
          (trust_score        (은폐 전략·         (역할별
           기반 의심 지시)      살해 대상 선정)      전략 지시)
                │                   │                   │
                └──────── Directive 발행 ────────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │   PlayerAgent × N (AI 플레이어)  │
                     │   StateGraph: run_agent → END │
                     └──────────────────────────────┘
```

**각 Agent의 역할 정의**

| Agent / Supervisor | 역할 |
|------------------|------|
| `CitizenSupervisor` | trust_score 최저 플레이어를 의심 대상으로 선정해 시민팀 AI 전원에게 지시 |
| `MafiaSupervisor` | 은폐 전략 지시 + Detective/Doctor 우선 살해 대상 선정 |
| `NeutralSupervisor` | Jester(처형 유도) / Spy(도청 정보 활용) 역할별 전략 지시 |
| `PlayerAgent` | 페르소나 + RAG 컨텍스트 + Supervisor 지시문을 종합해 자율 판단 |
| `GameInsightAgent` | 게임 종료 후 LangGraph(gate→analyze→mark)로 승리 패턴 RAG 추가 |

**Tool Calling / ReAct 활용**

`bind_tools([send_chat, submit_vote, use_ability])` 로 LLM이 직접 게임 상태를 변경하는 MCP Tool을 호출합니다. Tool 호출이 없으면 `with_structured_output(AgentDecision)` Fallback으로 구조화 출력을 받습니다.

**Memory 활용**

- **단기 메모리**: 최근 20개 채팅 히스토리를 LLM 컨텍스트에 포함
- **장기 메모리**: Redis Checkpointer(`MAFIA_USE_REDIS_CHECKPOINTER=1`)로 LangGraph 상태 영속화
- **팀 공유 메모리**: Supervisor가 받은 Report를 GameState에 누적, 팀 전원이 공유

---

### **2.3 RAG 구성**

**데이터 수집 및 전처리 파이프라인**

```
정적 지식베이스 (docs/rag_knowledge/ — 21개 .md 문서)
├── strategies/      (7개) 직업별 전략 — detective, doctor, mafia 등
├── speech_patterns/ (6개) 발언 스타일별 예시 — 논리형, 감정형, 공격형 등
├── situations/      (6개) 상황별 대응 — 열세 역전, 마피아 은폐 등
└── rules/           (2개) 게임 룰 문서 — Agent 조회용

런타임 지식베이스 (GameInsightAgent 자동 생성)
└── 게임 종료 후 승리 패턴 자동 추출 → ChromaDB 추가 (source="runtime")
```

각 문서는 YAML frontmatter에 `role`, `team`, `speech_style`, `category` 메타데이터를 포함하며, 인덱싱 시 ChromaDB 메타데이터 필터로 활용합니다.

**임베딩 모델 및 Vector DB**

| 항목 | 선택 | 이유 |
|-----|------|------|
| Vector DB | ChromaDB (PersistentClient) | 로컬 영속화, Docker Volume 연동 |
| 임베딩 모델 | `paraphrase-multilingual-mpnet-base-v2` | 한국어 게임 발언/전략 문서 처리 |
| 컬렉션 | `ai_mafia_knowledge` | static + runtime 문서 통합 관리 |

**검색 로직과 응답 생성 방식**

PlayerAgent가 LLM 호출 직전, 현재 Phase·Round·역할·Supervisor 지시를 기반으로 `retrieve_strategies(situation, k=3)`를 호출해 Top-3 전략 문서를 가져옵니다. 이 결과는 `rag_context`로 LLM human_prompt에 직접 주입됩니다.

---

### **2.4 서비스 개발 및 패키징 계획**

**UI 개발 (Streamlit)**

- 실시간 채팅 패널: WebSocket으로 AI 발언 스트림 표시
- 역할 정보 패널: 자신의 역할, 팀 표시 (마피아는 팀원 공개)
- 투표 패널: 생존자 목록 + 투표 버튼
- 신뢰도 점수 시각화: trust_score 게이지 (AI 플레이어 분석 정보)
- 사망 역할 공개: 처형/사망 시 역할 공개 애니메이션

**Backend 및 배포**

```
FastAPI (HTTP REST + WebSocket)
├── POST /game/create   — 게임 생성
├── GET  /health        — 서비스 상태 (llm_provider, rag_status)
├── WS   /ws/{game_id}  — 실시간 이벤트 Push
├── POST /game/{id}/chat   — 채팅
├── POST /game/{id}/vote   — 투표
└── POST /game/{id}/ability — 능력 사용

Docker Compose
├── redis    — LangGraph Checkpointer + 게임 아카이브
├── backend  — FastAPI (Cursor 담당)
└── frontend — Streamlit (Gemini 담당)
```

**환경 관리**

- `.env` 기반 환경변수 분리 (API 키, Redis URL, LLM Provider 등)
- `MAFIA_LLM_PROVIDER=anthropic|azure` 전환으로 제출 환경 대응

---

### **2.5 선택적 확장 기능**

**A. Structured Output / Function Calling (Advanced LLM)**

`with_structured_output(AgentDecision)` 을 전 노드에 적용해 LLM 응답의 구조적 일관성을 보장합니다. `confidence` 필드로 AI의 확신도를 수치화하여 UI에 표시합니다.

**B. MCP (Model Context Protocol) 기반 도구 연결**

`MCPGameTools` 클래스가 게임 상태 조작 도구를 MCP 인터페이스로 제공합니다:

```python
@tool send_chat(content, channel)   # 글로벌/마피아 채널 발언
@tool submit_vote(target_id)        # 투표 제출
@tool use_ability(ability, target)  # 역할 능력 사용
@tool report_to_supervisor(content) # Supervisor에게 상황 보고
```

LLM이 Tool을 자율 선택하고, `bind_tools` + `tool_calls` 파싱으로 실제 게임 상태를 직접 변경합니다.

**C. A2A (Agent-to-Agent) 협업 구조**

Supervisor → Agent 단방향 지시 + Agent → Supervisor 보고의 양방향 A2A 협업 구조:

```
PlayerAgent ──[Report]──▶ Supervisor (상황 보고)
Supervisor  ──[Directive]──▶ PlayerAgent (전략 지시)
```

`report_to_supervisor()` MCP 도구로 Agent가 자발적으로 의심 정보·관찰 내용을 Supervisor에게 보고하고, Supervisor는 이를 다음 Phase 지시에 반영합니다.

---

## **3. 주요 기능 및 동작 시나리오**

### **3.1 사용자 시나리오 (Use Case Scenario)**

**시나리오: 혼자 접속한 사용자가 마피아 게임을 완주하기까지**

```
[1] 게임 생성
    사용자 → POST /game/create (6인, 인간 1 + AI 5)
    시스템 → 직업 배정 (마피아 1, 경찰 1, 의사 1, 시민 3)

[2] 1라운드 낮 채팅 (Phase: DAY_CHAT)
    Supervisor → 팀별 전략 지시문 발행
    AI 5명 → RAG 전략 + 지시문 참조해 순서대로 발언
    사용자 → 채팅 입력으로 참여 가능
    (예) 마피아 AI: "ai_3이 어제 너무 조용했어, 의심스럽지 않나요?"
         시민 AI: "저도 동의해요, ai_3 먼저 조사해봐야 할 것 같아요."

[3] 낮 투표 (Phase: DAY_VOTE)
    전원 투표 → 최다 득표자 처형 → 역할 공개

[4] 밤 (Phase: NIGHT_ABILITY)
    경찰: 조사 대상 선택 → 마피아 여부 확인 (Report로 자신에게만 공개)
    의사: 보호 대상 선택
    마피아: MafiaSupervisor의 살해 대상 지시에 따라 공격

[5] 다음 라운드 반복 → 승리 조건 달성 시 종료

[6] 게임 종료
    승리팀 발표, AI 신뢰도 점수, 내부 추론 로그 공개
    GameInsightAgent → 백그라운드에서 승리 패턴 RAG 추가 (다음 게임 학습)
```

---

### **3.2 시스템 구조도 / Multi-Agent 다이어그램**

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Mafia Online                          │
│                                                                  │
│  [Streamlit Frontend]  ←──WebSocket──→  [FastAPI Backend]       │
│   실시간 채팅 UI                          GameRunner (Phase 루프) │
│   투표 패널                                     │                │
│   신뢰도 시각화                      ┌──────────▼──────────┐    │
│                                     │     AgentGraph       │    │
│                                     │  ┌─────────────────┐ │    │
│                                     │  │ CitizenSupervisor│ │    │
│                                     │  │ MafiaSupervisor  │ │    │
│                                     │  │ NeutralSupervisor│ │    │
│                                     │  └────────┬────────┘ │    │
│                                     │  Directive │          │    │
│                                     │  ┌─────────▼──────┐  │    │
│                                     │  │ PlayerAgent × N │  │    │
│                                     │  │ LangGraph       │  │    │
│                                     │  │ StateGraph      │  │    │
│                                     │  └────────┬────────┘  │    │
│                                     └───────────┼───────────┘    │
│                                                 │                │
│   [ChromaDB]  ←── RAG 검색 ──────────────────────┘                │
│   [Redis]     ←── Checkpointer + Archive                        │
│   [LLM API]   ←── Claude / Azure OpenAI                         │
└─────────────────────────────────────────────────────────────────┘
```

---

### **3.3 서비스 플로우**

```
사용자 요청 (채팅/투표/능력)
    │
    ▼
FastAPI 엔드포인트 수신
    │
    ▼
GameEngine 상태 업데이트 (engine.apply_action)
    │
    ▼
GameRunner Phase 판단
    ├─ DAY_CHAT  → AgentGraph.run_day_chat_round()
    ├─ DAY_VOTE  → AgentGraph.run_vote_round()
    ├─ NIGHT_*   → AgentGraph.run_night_*_round()
    │
    ▼
Supervisor → Directive 발행 (팀 전략 지시)
    │
    ▼
PlayerAgent.run(AgentInput)
    ├─ RAG 검색 (ChromaDB, k=3)
    ├─ LLM 호출 (bind_tools 또는 with_structured_output)
    └─ AgentDecision 반환
    │
    ▼
GameState 업데이트 (채팅 추가 / 투표 반영 / 능력 효과 적용)
    │
    ▼
WebSocket Broadcast → Streamlit 실시간 UI 갱신
    │
    ▼
Phase 종료 → supervisor_replan() (상황 재진단)
    │
    ▼
게임 종료 시 → GameArchiver(Redis) + GameInsightAgent(RAG 학습)
```

---

## **4. 실행 결과**

**서비스 실행 방법**

```bash
# 환경변수 설정
cp .env.example .env
# .env에 ANTHROPIC_API_KEY 또는 AOAI_* 입력

# 실행
docker-compose up --build

# 접속
# Frontend: http://localhost:8501
# Backend API 문서: http://localhost:8000/docs
# 서비스 상태: http://localhost:8000/health
```

**실행 로그 예시 (멀티 에이전트 동작)**

```
[POD=mafia-backend] 게임 생성 완료 — game_id=abc123 players=6
[POD=mafia-backend] AgentGraph 초기화 — supervisors=[Citizen, Mafia, Neutral] agents=['ai_1'~'ai_5']
[POD=mafia-backend] Phase 전환 — phase=day_chat round=1
[POD=mafia-backend] CitizenSupervisor → directives=5 targets=['ai_1','ai_2','ai_3','ai_4','ai_5']
[POD=mafia-backend] invoke agent=ai_1 phase=day_chat
[POD=mafia-backend] rag retrieved k=3
[POD=mafia-backend] llm_decide agent=ai_1 phase=day_chat
[POD=mafia-backend] tool_call name=send_chat args={'content': 'ai_3이 수상해 보입니다...'}
```

**주요 시나리오별 동작 결과**

| 시나리오 | 결과 |
|---------|------|
| AI가 경찰 역할일 때 조사 결과 활용 | Report에 저장 → Supervisor가 다음 Phase 지시에 반영 |
| 마피아 AI가 의심받을 때 | MafiaSupervisor의 은폐 전략 지시 → "저도 ai_3이 의심스럽습니다" 발언 전환 |
| 시민 AI의 trust_score 기반 표적 | 가장 낮은 trust_score 플레이어를 의심 발언으로 집중 타겟 |
| 게임 종료 후 RAG 학습 | GameInsightAgent가 승리 패턴 2~3개 문서 자동 생성 후 ChromaDB 추가 |

---

## **5. 추가 아이디어 (선택)**

**단기 개선 아이디어**

- **스트리밍 응답**: `stream()` 적용으로 AI 발언이 타이핑하듯 실시간 표시 → 몰입감 극대화
- **병렬 에이전트 실행**: `asyncio.gather()`로 여러 AI 동시 처리 → 게임 진행 속도 향상
- **LangGraph 조건부 엣지**: `add_conditional_edge`로 Phase 분기를 LangGraph 네이티브 구조로 전환

**중장기 확장 아이디어**

- **Redis Pub/Sub 기반 멀티 POD**: 현재 in-memory 구조를 Redis 공유 상태로 마이그레이션 → 수평 확장 가능
- **AI 관전 모드**: 사람 없이 AI 전원으로 게임 진행, 전략 발전 과정을 시간 가속으로 시뮬레이션
- **사용자 통계 대시보드**: 승률, trust_score 변화, 역할별 생존율 등 분석 리포트
- **커스텀 역할 추가**: RAG 지식베이스에 새 역할 문서 추가만으로 신규 역할 자동 지원
