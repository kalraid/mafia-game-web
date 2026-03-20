# RAG vs 저장소 설계 결정서 (RAG_AND_STORAGE_DESIGN)

> **문서 버전**: v1.1
> **작성일**: 2026-03-18
> **최종 업데이트**: 2026-03-20 (§8 동적 RAG 업데이트 설계 추가)
> **목적**: RAG 활용 범위 명확화 + 평가 기준 반영

---

## 1. RAG가 맞는 것 vs 아닌 것 — 판단 기준

```
RAG가 적합한 데이터:
  ✅ 정적(Static)이고 게임 간 공유되는 지식
  ✅ 의미 기반 유사도 검색이 필요한 것
  ✅ "이 상황과 비슷한 사례/전략은?" 같은 질의

RAG가 부적합한 데이터:
  ❌ 게임별로 달라지는 동적(Dynamic) 상태
  ❌ 빠른 키-값 조회가 필요한 것
  ❌ 실시간 변경이 잦은 것
```

---

## 2. 데이터 분류표

| 데이터 | 저장소 | 이유 |
|--------|--------|------|
| **마피아 전략 전술** | ✅ RAG | 게임 간 공유, 의미 검색 필요 |
| **역할별 발언 패턴** | ✅ RAG | 의미 유사도로 상황에 맞는 패턴 검색 |
| **상황별 행동 사례** | ✅ RAG | "3:2 상황에서 마피아 전략" 같은 유사 사례 검색 |
| **AI 페르소나 발언 예시** | ✅ RAG | 말투/성격별 예시 문장 검색 |
| **게임 룰 정의** | ✅ RAG | Agent가 룰을 조회할 때 |
| **심리전 패턴** | ✅ RAG | "의심 돌리기", "방어 발언" 등 전술 패턴 |
| | | |
| **현재 게임 상태** | 🔵 In-Memory | 실시간 변경, 빠른 조회 필요 |
| **살아있는 플레이어 목록** | 🔵 In-Memory | 매 Phase마다 변경 |
| **투표 집계** | 🔵 In-Memory | 실시간 카운트 |
| **현재 Phase/타이머** | 🔵 In-Memory | 매초 변경 |
| **게임 내 채팅 히스토리** | 🔴 Redis | 게임 세션 단위 유지, 멀티턴 컨텍스트 |
| **Agent 단기 기억** | 🔴 Redis | 이번 게임 내 관찰 기록 (누가 수상했나 등) |
| **게임 프롤로그/이벤트 로그** | 🔴 Redis | 게임 종료 후 결과 조회 가능하게 |
| **플레이어별 trust_score** | 🔴 Redis | 라운드별 업데이트, Agent 간 공유 |
| **슈퍼바이저 directive** | 🔴 Redis | Agent들이 공유해서 읽어야 함 |

---

## 3. RAG 지식베이스 상세 구성

### 3.1 카테고리별 문서 설계

```
rag/knowledge/
│
├── strategies/
│   ├── mafia_basic.md          # 마피아 기본 전술 (희생양 만들기, 알리바이 등)
│   ├── mafia_advanced.md       # 고급 전술 (경찰 역이용, 소수 마피아 생존법)
│   ├── citizen_deduction.md    # 시민 추리 패턴 (침묵 분석, 발언 패턴 분석)
│   ├── detective_tactics.md    # 경찰 정보 공개 전략 (언제 밝힐까)
│   ├── doctor_protection.md    # 의사 보호 우선순위 전략
│   ├── jester_tactics.md       # 광대 의심 유도 발언법
│   └── spy_survival.md         # 스파이 생존 전략
│
├── speech_patterns/
│   ├── aggressive.md           # 공격적 말투 발언 예시 50개
│   ├── cautious.md             # 조심스러운 말투 발언 예시 50개
│   ├── logical.md              # 논리형 발언 예시 50개
│   ├── emotional.md            # 감정형 발언 예시 50개
│   ├── deflection.md           # 의심 돌리기 발언 패턴
│   └── defense.md              # 방어 발언 패턴
│
├── situations/
│   ├── early_game.md           # 초반(1~2라운드) 전략
│   ├── mid_game.md             # 중반 전략
│   ├── endgame_citizen.md      # 후반 시민 생존 전략
│   ├── endgame_mafia.md        # 후반 마피아 역전 전략
│   ├── ratio_3_2.md            # 인원 비율별 대응 전략
│   └── last_mafia.md           # 마피아 1명 남은 상황
│
└── rules/
    ├── game_rules.md           # 게임 룰 전체 (Agent가 조회용)
    └── role_abilities.md       # 직업별 능력 상세
```

### 3.2 RAG 쿼리 예시

```python
# Agent가 발언 생성 전 RAG 조회 예시
query = f"""
현재 상황: 라운드 {round}, 마피아 {mafia_count}명, 시민 {citizen_count}명
내 역할: {my_role}
최근 대화: {recent_chat_summary}
필요한 전략: 발언 방향
"""
# → speech_patterns/ + situations/ 에서 유사 사례 Top-3 검색

# 슈퍼바이저가 전략 수립 시 RAG 조회
query = f"마피아 {mafia_count}명 vs 시민 {citizen_count}명 상황에서 최우선 제거 대상 전략"
# → strategies/mafia_*.md 에서 검색
```

---

## 4. 게임 프롤로그 & 플레이어 정보 — 저장 위치 결론

> **결론: Redis (게임 세션 단위 저장)**

### 이유
- 프롤로그는 **이번 게임에서만** 유효한 정보
- 게임 종료 후 결과 조회나 로그 확인이 필요
- Agent가 "이번 게임의 맥락"을 빠르게 조회해야 함
- RAG에 넣으면 다른 게임의 정보와 섞여 노이즈 발생

### Redis 키 설계
```
game:{game_id}:state          → 전체 게임 상태 JSON
game:{game_id}:prologue       → 게임 시작 시 설정 (인원, 직업 배분 결과)
game:{game_id}:players        → 플레이어별 정보 (역할, 생존, trust_score)
game:{game_id}:chat:{round}   → 라운드별 채팅 히스토리
game:{game_id}:events         → 게임 이벤트 로그 (사망, 투표 결과 등)
game:{game_id}:directives     → 슈퍼바이저 → Agent 지시
agent:{game_id}:{agent_id}:memory  → Agent 개인 관찰 메모리
```

### LangGraph Checkpointer 연동
```python
# Redis를 LangGraph checkpointer로 연동
from langgraph.checkpoint.redis import RedisSaver

checkpointer = RedisSaver(redis_client)
graph = graph.compile(checkpointer=checkpointer)

# thread_id = game_id + agent_id 조합으로 Agent별 상태 독립 유지
config = {"configurable": {"thread_id": f"{game_id}_{agent_id}"}}
```

---

## 5. 메모리 계층 구조 (최종 정리)

```
┌─────────────────────────────────────────────────────┐
│  L1. Agent 실행 컨텍스트 (In-Memory, 단일 호출)      │
│      현재 호출에 필요한 정보만 로드                   │
│      game_state 스냅샷, 최근 채팅 10개, directive    │
├─────────────────────────────────────────────────────┤
│  L2. 게임 세션 메모리 (Redis, 게임 종료까지 유지)    │
│      전체 채팅 히스토리, 이벤트 로그, trust_score    │
│      LangGraph Checkpointer로 연동                   │
├─────────────────────────────────────────────────────┤
│  L3. 전략 지식베이스 (RAG / ChromaDB, 영구 유지)     │
│      전략 문서, 발언 패턴, 상황별 사례, 룰 문서      │
│      게임 간 공유, 의미 기반 검색                    │
└─────────────────────────────────────────────────────┘
```

---

## 6. 평가 피드백 반영 사항 (아래 섹션 참조)

> ⚠️ 이 문서는 이전 프로젝트 평가 피드백을 분석하여  
> 현재 프로젝트 설계에 선제적으로 반영한 결과를 담고 있습니다.  
> 상세 내용은 `EVALUATION_REFLECTION.md` 참조

---

## 7. 설계 결정 요약

| 질문 | 결론 |
|------|------|
| 게임 프롤로그/플레이어 정보를 RAG에? | ❌ Redis (게임 세션 단위) |
| RAG는 전략만? | ✅ 전략 + 발언 패턴 + 상황 사례 + 룰 문서 |
| 채팅 히스토리 저장소 | 🔴 Redis + LangGraph Checkpointer |
| Agent 단기 기억 | 🔴 Redis (per agent, per game) |
| 실시간 게임 상태 | 🔵 In-Memory (Phase, 타이머, 투표 집계) |
| 실전 게임 데이터 → RAG? | ✅ §8 GameInsightAgent로 자동 추가 (source=runtime) |

---

## 8. 동적 RAG 업데이트 — GameInsightAgent 설계 (Phase 8)

### 8.1 개요

정적 지식베이스(20개 문서)는 게임 간 공유되는 범용 전략을 담지만,
실전 판에서 나온 패턴은 점차 쌓일수록 AI 플레이 품질을 더욱 향상시킬 수 있음.
`GameInsightAgent`가 게임 종료 후 백그라운드로 실행되어 인사이트를 자동으로 RAG에 추가.

### 8.2 새 Redis 키 스키마

| 키 | 타입 | 내용 | TTL |
|----|------|------|-----|
| `mafia:game_archive:{game_id}` | String (JSON) | 완료된 GameState 전체 | 30일 |
| `mafia:game_analysis:processed` | Set | 분석 완료된 game_id 목록 | 없음 |

### 8.3 파이프라인 흐름

```
GameEngine (in-memory GameState)
  │
  ▼ [게임 종료 hook — runner.py]
  │
  ▼ Redis  mafia:game_archive:{game_id}  (JSON, TTL 30일)
  │
  ▼ GameInsightAgent  (mafia:game_analysis:processed SET으로 중복 방지)
  │
  ▼ LLM (Claude) — bind_tools + with_structured_output
  │    ├── read_game_record()       Redis 게임 기록 조회
  │    ├── search_existing_rag()    기존 RAG 중복 방지 검색
  │    └── write_insight_doc()      RAGStore에 문서 추가
  ▼
  ChromaDB  ai_mafia_knowledge 컬렉션  (source="runtime")
```

### 8.4 LangGraph StateGraph 구조

```
[load_pending] → [analyze] ──(tool_calls 루프)──→ [write_rag] → [mark_done] → END
```

- **load_pending**: Redis에서 미분석 game_id 목록 조회
- **analyze**: Claude LLM + bind_tools 로 게임 기록 분석 (ReAct 루프)
- **write_rag**: 생성된 인사이트 문서를 RAGStore에 추가
- **mark_done**: 처리 완료 game_id를 `mafia:game_analysis:processed` SET에 추가

### 8.5 RAG 문서 메타데이터 구분

| 필드 | 정적 지식 | 실전 데이터 |
|------|----------|-----------|
| `source` | `"static"` | `"runtime"` |
| `category` | strategies / situations 등 | strategy / situation / speech_pattern |
| `game_id` | 없음 | 원본 game_id |
| `insight_type` | 없음 | winning_pattern / speech_pattern / voting_pattern |

### 8.6 생성 문서 예시

```markdown
# 마피아 2인 열세 역전 전략 (실전 데이터)

category: strategy
source: runtime
game_id: game_abc123
insight_type: winning_pattern
tags: [mafia, endgame, 2v4]

## 상황
라운드 3, 마피아 2명 vs 시민 4명.

## 관찰된 패턴
- 마피아 A가 경찰 의심을 받는 시민 B에게 공격적으로 동조 → 투표 집중 유도
- 마피아 B는 침묵 전략으로 의심 분산
- 결과: 3연속 시민 처형 성공 후 역전
```

### 8.7 메모리 계층 갱신

```
┌─────────────────────────────────────────────────────────────────┐
│  L1. Agent 실행 컨텍스트 (In-Memory, 단일 호출)                  │
├─────────────────────────────────────────────────────────────────┤
│  L2. 게임 세션 메모리 (Redis, 게임 종료까지 유지)                │
│      + mafia:game_archive:{game_id}  (게임 종료 후 30일 보관)    │
│      + mafia:game_analysis:processed (중복 분석 방지)            │
├─────────────────────────────────────────────────────────────────┤
│  L3. 전략 지식베이스 (RAG / ChromaDB, 영구 유지)                 │
│      source=static  : 정적 지식 20개 (docs/rag_knowledge/)       │
│      source=runtime : 실전 인사이트 (GameInsightAgent 자동 추가) │
└─────────────────────────────────────────────────────────────────┘
```

**구현 지시**: `WORK_ORDER_CURSOR.md` C-10 참조
