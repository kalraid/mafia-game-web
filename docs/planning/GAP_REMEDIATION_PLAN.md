# 기획·코드 격차 및 리뷰 반영 계획 (GAP_REMEDIATION_PLAN)

> **목적**: 최종 프로젝트 코드 리뷰 결과를 저장하고, **충족 / 부분충족 / 미충족** 항목을 추적하며 실행 가능한 GAP 작업으로 정리한다.  
> **기준일**: 2026-04-06  
> **참조 문서**: `PROPOSAL.md`, `AGENT_DESIGN.md`, `RAG_AND_STORAGE_DESIGN.md`, `UI_DESIGN.md`, `TASK_PLAN.md`

---

## 1. 검토 요약 (영역별)

| 영역 | 리뷰 판정 | 한 줄 메모 |
|------|-----------|------------|
| 주제 선정 및 기획/설계 | **충족** | 문제 정의·에이전트 역할·차별점·기술별 문서가 코드와 연결됨 |
| Prompt Engineering | **충족** *(고급 기법 제외)* | 역할·페이즈 구조화·structured output 충족; few-shot 등은 미적용 |
| RAG | **부분충족** | 인덱싱·전처리·검색·에이전트 주입 충족; **메타 필터·MMR 등 고도화**는 설계 대비 구현 단순 |
| LangChain/LangGraph Agent | **부분충족** | 멀티에이전트·툴콜·Checkpointer·도메인 로직 충족; **메인 게임 루프는 `GameRunner` 수동 페이즈**로 LangGraph 범위가 제한 |
| 서비스 패키징·UI | **충족** | Streamlit 흐름·에러/검증·디렉터리 구조 적절 |

**종합**: Supervisor–PlayerAgent·게임 종료 후 Insight RAG 적재 등 차별점이 명확. 완성도를 더 올리려면 **RAG 고도화**와 **고급 프롬프팅**이 우선 후보.

---

## 2. 평가 체크포인트 매핑 (리뷰 원문 기준)

### 2.1 주제·기획/설계 — 모두 충족

- 문제 정의·적용 시나리오: `PROPOSAL.md` 등
- Agent 목표/역할/핵심 기능: `AGENT_DESIGN.md`, `PROPOSAL.md`
- 차별화: 팀 지휘·종료 후 RAG·추론 공개 → `analysis_agent.py`, `runner.py` 등과 연결
- 기술별 설명: `PROPOSAL`, `AGENT_DESIGN`, `RAG_AND_STORAGE_DESIGN`, `UI_DESIGN`

### 2.2 Prompt Engineering

| 체크 | 결과 | 근거 |
|------|------|------|
| 역할 기반 프롬프트 | ✅ | `player_agent.py` — `persona`(speech_style, aggression 등) |
| **고급 기법 (few-shot, exemplar, self-consistency)** | ❌ | 동 파일·프롬프트 구성에서 **미확인** → **GAP-PE-01** |
| 입력 일관성(페이즈 분기·허용 필드) | ✅ | `phase_instruction` — DAY_CHAT / VOTE / NIGHT_* |
| 출력 형식 | ✅ | `AgentDecision` + `with_structured_output` |

### 2.3 RAG

| 체크 | 결과 | 근거 |
|------|------|------|
| Vector DB + 임베딩 인덱싱 | ✅ | `rag/store.py` — ChromaDB, SentenceTransformer |
| 전처리·문서 구조화 | ✅ | `_extract_frontmatter`, 메타데이터 |
| 쿼리 검색 | ✅ | `retriever.py`, `player_agent._fetch_rag_context_raw` |
| 에이전트 통합 | ✅ | `rag_context` → `human_prompt`, `runner` 디버그 노출 |
| **정확도/사용성 고도화 (필터·MMR 등)** | ⚠️ | `AGENT_DESIGN.md` §5.2·`RAG_AND_STORAGE_DESIGN` 등 **계획 대비** `retriever`/`store`는 **similarity 중심** → **GAP-RAG-01** |

### 2.4 LangChain / LangGraph

| 체크 | 결과 | 근거 |
|------|------|------|
| LangChain 활용 | ✅ | bind_tools, structured output, 메시지, `analysis_agent` |
| **LangGraph로 “전체” 에이전트 구조** | ⚠️ | `graph.py`, `analysis_agent`에 StateGraph 있으나 **메인 게임 흐름은 `game/runner.py` 페이즈 루프** → **GAP-LG-01** (문서 정합·장기 과제) |
| Multi-Agent | ✅ | `graph.py` + `supervisors/*.py` |
| Tool / MCP 호출 | ✅ | `send_chat`, `submit_vote`, `use_ability`, `report_to_supervisor` 등 |
| Checkpointer / 멀티턴 | ✅ | RedisSaver + `thread_id` (`graph.py`) |
| 도메인 특화 | ✅ | 슈퍼바이저, `analysis_agent` |

### 2.5 서비스 패키징 — 모두 충족

- UI: `frontend/app.py`, `pages/*`
- 사용자 흐름: `chat_area`, `status_panel`, lobby/result 등
- 에러·검증: `frontend/utils.py` (`handle_request_error` 등), `backend/main.py` Pydantic, lobby 버튼 상태
- 구조: `backend/agents|game|rag|supervisors`, `frontend/components|pages`, `docs/planning`

---

## 3. 우선순위 정의

| 우선순위 | 의미 |
|----------|------|
| **P1** | 평가 루브릭에서 **명시적 미충족(❌)** 에 해당 |
| **P2** | **부분충족(⚠️)** — 설계 문서와 구현 간격 |
| **P3** | 아키텍처 대개편(예: 전 게임 단일 LangGraph) — 비용 대비 선택 |

---

## 4. GAP 백로그 (실행 단위)

| ID | 우선순위 | 영역 | 갭 내용 | 권장 조치 | 산출물·완료 기준 |
|----|----------|------|---------|-----------|------------------|
| **GAP-PE-01** | P1 | Prompt | few-shot / exemplar / self-consistency **미적용** | 페이즈·역할별로 짧은 예시 블록을 프롬프트 모듈에 추가하거나, 품질 실험 후 1~2개 페이즈에만 도입 | `player_agent.py` 또는 분리된 prompt 템플릿 + 회귀 시나리오(선택) |
| **GAP-RAG-01** | P2 | RAG | 설계상 **메타데이터 필터·MMR** 등과 달리 **유사도 검색 위주** | (a) `Chroma` where 필터 + 검색 파이프라인 보강 (b) 또는 설계 문서에 “현행은 baseline similarity”를 명시하고 고도화를 Phase로 분리 | `retriever.py` / `store.py` 또는 `AGENT_DESIGN`·`RAG_AND_STORAGE_DESIGN` 현행화 |
| **GAP-LG-01** | P2 | LangGraph | 리뷰 관점에서 **메인 오케스트레이션이 runner 수동 루프** | `AGENT_DESIGN.md` §1.1·`TECH_ARCHITECTURE.md`에 **의도적 범위**가 이미 있으면 **체크만**; 없으면 한 절 보강. 전체 StateGraph 전환은 P3 | 문서 정합 확인 또는 TASK_PLAN 백로그 문장 |
| **GAP-RANK-01** | P3 | RAG | 리뷰 종합 의견의 **reranking** | 크로스인코더/가벼운 rerank 또는 상위 k 재정렬 — 리소스 허용 시 | 실험 PR 또는 문서에 “향후 과제”로만 기록 |

**연동**: 병렬 AI 턴(`asyncio.gather`) 등은 `TASK_PLAN.md` **I-19**(보류)와 중복되지 않게, GAP-LG-01은 **오케스트레이션 모델(누가 그래프를 소유하나)** 정합에 한정한다.

---

## 5. 권장 실행 순서

1. **GAP-LG-01** — 문서만으로 끝날 수 있음(이미 반영 여부 확인).  
2. **GAP-PE-01** — 데모·채점 대비 체감 큰 경우 우선.  
3. **GAP-RAG-01** — 인덱스 규모·역할 다양성이 커질수록 효용 증가.  
4. **GAP-RANK-01** — 선택.

---

## 6. 복사용 체크리스트

```
[ ] GAP-PE-01  고급 프롬프팅 (few-shot / exemplar / self-consistency) 도입 또는 범위 명시
[ ] GAP-RAG-01  RAG 메타 필터·MMR(및 필요 시 rerank) 구현 또는 설계-구현 문서 정합
[ ] GAP-LG-01  LangGraph 적용 범위(Runner vs 서브그래프) 문서·TASK_PLAN 재확인
[ ] GAP-RANK-01  (선택) RAG reranking 실험 또는 향후 과제로만 기록
```

---

## 7. 역할 힌트 (분업)

| GAP | 주 담당 |
|-----|---------|
| GAP-PE-01 | Cursor (`backend/agents/`) |
| GAP-RAG-01 | Cursor (`backend/rag/`) + 기획 문서 동기화 시 Claude |
| GAP-LG-01 | Claude (`docs/planning/`) + 필요 시 Cursor |
| GAP-RANK-01 | Cursor (선택) |

`WORK_ORDER_CURSOR.md` / `WORK_ORDER_GEMINI.md`에 위 ID를 인용해 지시하면 추적이 쉽다.
