# AI Agent 설계 명세서 (AGENT_DESIGN)

> **문서 버전**: v1.0  
> **작성일**: 2026-03-18

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
                    │         (각각 독립 LangGraph Node)      │
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
  → 발언 타이밍: 랜덤 딜레이(1~15초) + Agent 성격에 따른 가중치

SubGraph: vote_graph
  → 투표 Phase: 각 Agent가 투표 대상 결정
  → 슈퍼바이저 의견 참고 후 최종 투표

SubGraph: night_graph
  → 밤 Phase: 마피아 협의 → 능력 사용 → 결과 계산

Node: win_condition_checker
  → 각 Phase 종료 후 승리 조건 확인
```

### 2.2 Agent Node 구조 (개별 AI 플레이어)

각 Agent는 다음 구조로 동작:

```
Agent Node 입력:
  - game_state: 현재 게임 전체 상태
  - my_state: 내 직업, 생존 여부, 보유 정보
  - supervisor_directive: 슈퍼바이저로부터의 지시
  - chat_history: 최근 N개 채팅 (컨텍스트 윈도우)
  - rag_context: RAG에서 가져온 전략 지식

Agent 처리 단계:
  1. [RAG] 현재 상황과 유사한 전략 사례 검색
  2. [Reasoning] 발언 또는 행동 계획 수립
  3. [A2A Check] 슈퍼바이저 지시 확인 및 통합
  4. [Output] 발언 텍스트 or 능력 사용 결정 반환

Agent Node 출력:
  - speech: str (채팅 발언 내용, 없으면 None)
  - action: dict (능력 사용 정보)
  - vote: str (투표 대상 player_id)
  - internal_notes: str (Agent 내부 추론, 디버그용)
```

---

## 3. 슈퍼바이저 (Supervisor) 설계

### 3.1 시민 슈퍼바이저

**역할**: 시민 진영 전체의 전략 수립 및 조율

**입력**:
- 전체 게임 상태
- 경찰/의사로부터의 정보 보고 (A2A)
- 라운드별 채팅 분석

**매 낮 Phase 수행**:
1. 의심 대상 목록 업데이트 (trust score 기반)
2. 각 시민 Agent에게 발언 전략 지시 (A2A)
   - "AI_3를 집중 추궁하라"
   - "AI_7을 믿는 척하며 방어하라"
3. 경찰에게 다음 조사 대상 제안

**매 밤 Phase 수행**:
1. 의사에게 보호 대상 추천
2. 경찰 조사 결과 수집 및 공유 계획 수립

---

### 3.2 마피아 슈퍼바이저

**역할**: 마피아 진영의 은폐 전략 및 공격 대상 결정

**입력**:
- 전체 게임 상태
- 각 마피아 Agent의 관찰 보고 (A2A)

**매 낮 Phase 수행**:
1. 마피아 신분 은폐 전략 수립
   - "AI_2는 강력하게 시민 주장"
   - "AI_9은 AI_4를 의심하여 주의 분산"
2. 희생양(scapegoat) 대상 선정 및 각 마피아에게 지시

**매 밤 Phase 수행**:
1. 각 마피아의 공격 추천 대상 수집
2. 최우선 제거 대상 결정 (경찰 > 의사 > 영향력 큰 시민)
3. 최종 공격 대상 1명 확정 및 전달

**의사결정 우선순위**:
```
1순위: 경찰 (확인된 경우)
2순위: 의사 (확인된 경우)
3순위: 발언력이 높은 시민 (채팅 분석 기반)
4순위: 무작위 시민
```

---

### 3.3 중립 슈퍼바이저

**역할**: 중립 Agent(광대, 스파이)의 개인 목표 달성 지원

**광대 지원**:
- 의심받을 수 있는 발언 패턴 생성
- 투표 시 본인이 선택되도록 유도하는 전략

**스파이 지원**:
- 마피아 채널 정보 활용 전략 (생존 우선)
- 의심받지 않는 발언 전략

---

## 4. A2A (Agent-to-Agent) 통신 설계

### 4.1 통신 방식
- LangGraph의 **State Channel** 활용
- 슈퍼바이저가 GameState의 `directives` 필드에 지시 기록
- 각 Agent는 실행 시 자신에 해당하는 directive 읽기

### 4.2 Directive 구조
```json
{
  "target_agent": "agent_3",
  "from": "mafia_supervisor",
  "type": "speech_strategy",
  "content": "이번 낮에는 AI_7을 적극적으로 의심하는 발언을 해라. 근거는 AI_7이 첫 라운드에 침묵했다는 점을 활용해.",
  "priority": "high",
  "round": 2
}
```

### 4.3 A2A 통신 흐름
```
슈퍼바이저 → (directive 생성) → GameState.directives[]
Agent 실행 시 → 자신의 directive 필터링 → 지시 통합 → 행동 결정
Agent → (보고) → GameState.reports[]
슈퍼바이저 → reports 읽기 → 다음 전략 수립
```

---

## 5. RAG (Retrieval-Augmented Generation) 설계

### 5.1 지식베이스 구성

**문서 카테고리**:

| 카테고리 | 내용 | 예시 |
|---------|------|------|
| 마피아 전략 | 마피아 플레이 전술 | "경찰이 의심될 때 빨리 제거하라" |
| 시민 추리법 | 의심 단서 패턴 | "첫날 침묵한 플레이어는 마피아일 가능성" |
| 발언 패턴 | 역할별 자연스러운 발언 | "시민 발언 예시 50가지" |
| 게임 상황별 | 특정 상황 대응법 | "3:2 상황에서 시민이 살아남는 법" |
| 중립 전략 | 광대/스파이 전술 | "광대로서 의심받는 25가지 방법" |

### 5.2 RAG 활용 시점
- Agent가 발언 생성 전: 현재 게임 상황과 유사 전략 사례 검색
- 슈퍼바이저 전략 수립 시: 인원 구성별 최적 전략 검색
- 투표 결정 전: 유사 상황의 투표 패턴 참고

### 5.3 임베딩 전략
- 모델: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (한국어 지원)
- 벡터 DB: ChromaDB (로컬, 파일 기반)
- 검색 방식: 코사인 유사도, Top-K=3

### 5.4 RAG 쿼리 예시
```
상황: "라운드 2, 마피아 2명, 시민 5명, 경찰 생존, 의사 사망"
쿼리: "마피아가 경찰을 조기 제거해야 하는 상황에서의 전략"
결과: 관련 전략 문서 3개 → Agent 프롬프트에 컨텍스트로 주입
```

---

## 6. MCP (Model Context Protocol) Tool 설계

### 6.1 Game State Tools (Agent가 호출 가능)

```python
@mcp_tool
def get_alive_players() -> List[Player]:
    """현재 살아있는 플레이어 목록 반환"""

@mcp_tool
def get_chat_history(last_n: int = 20) -> List[ChatMessage]:
    """최근 N개 채팅 메시지 반환"""

@mcp_tool
def get_my_role(agent_id: str) -> Role:
    """내 직업 정보 반환"""

@mcp_tool
def get_current_phase() -> PhaseInfo:
    """현재 게임 Phase, 남은 시간 반환"""

@mcp_tool
def get_supervisor_directives(agent_id: str) -> List[Directive]:
    """슈퍼바이저로부터 받은 지시 목록 반환"""
```

### 6.2 Action Tools (Agent가 호출 가능)

```python
@mcp_tool
def send_chat(agent_id: str, content: str, channel: str = "global") -> bool:
    """채팅 메시지 전송"""

@mcp_tool
def submit_vote(agent_id: str, target_id: str) -> bool:
    """투표 제출"""

@mcp_tool
def use_ability(agent_id: str, ability: str, target_id: str) -> AbilityResult:
    """직업 능력 사용 (investigate, heal, attack 등)"""

@mcp_tool
def report_to_supervisor(agent_id: str, report: str) -> bool:
    """슈퍼바이저에게 보고"""
```

### 6.3 Supervisor-Only Tools

```python
@mcp_tool
def issue_directive(supervisor_id: str, target_agent: str, directive: Directive) -> bool:
    """슈퍼바이저 → Agent 지시 전달"""

@mcp_tool
def get_all_reports(supervisor_id: str) -> List[Report]:
    """소속 Agent들의 보고 수집"""

@mcp_tool
def analyze_trust_scores() -> Dict[str, float]:
    """전체 플레이어 신뢰도 분석 결과"""
```

---

## 7. Agent 페르소나 설계

각 AI Agent는 게임 시작 시 고유한 **페르소나**를 부여받아 일관된 말투와 성격을 유지.

### 7.1 페르소나 속성
```python
class AgentPersona(BaseModel):
    name: str              # "김철수", "이영희" 등 한국 이름
    speech_style: str      # "격식체", "반말", "조심스러운", "공격적"
    aggression: float      # 0.0(소극적) ~ 1.0(공격적)
    trust_tendency: float  # 0.0(의심많음) ~ 1.0(잘믿음)
    verbosity: float       # 0.0(과묵) ~ 1.0(수다)
    logic_style: str       # "감정형", "논리형", "직관형"
```

### 7.2 페르소나 예시

| 이름 | 말투 | 성격 | 특징 |
|------|------|------|------|
| 김민준 | 반말 | 공격적 | 주도적으로 토론 이끎 |
| 박서연 | 존댓말 | 조심스러움 | 조용하지만 날카로운 추론 |
| 이지호 | 반말 | 논리형 | 데이터 기반 분석 |
| 최수아 | 존댓말 | 감정형 | 분위기로 판단 |
| 정태양 | 반말 | 직관형 | 본능으로 마피아 찍기 |

---

## 8. Agent 실행 동시성

- 낮 Phase: 19개 Agent 순차 실행 (발언 타이밍 자연스러움)
  - 발언 순서: 랜덤 셔플 + 성격별 가중치
  - asyncio gather로 동시 추론, 순차 출력
- 밤 Phase: 역할별 병렬 실행
  - 마피아 협의: 마피아 Agent들만 병렬
  - 직업 능력: 전체 병렬 실행 → 결과 집계
