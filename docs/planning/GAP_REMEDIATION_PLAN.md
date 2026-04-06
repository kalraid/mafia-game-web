# 기획 대비 미흡 항목 — 작업 계획 (TODO)

> **목적**: `PROPOSAL.md` 본문은 유지한 채, 구현 점검 시 정리된 **기획–코드 간격**을 메우기 위한 실행 계획이다.  
> **기준일**: 2026-04-06  
> **참조**: 제출 기획서 하단 「부록 — 기획서 대비 구현 차이」에 대응하는 백로그.

---

## 우선순위 정의

| 우선순위 | 의미 |
|----------|------|
| **P0** | 기획서 기술 주장(에이전트·MCP)과 직접 충돌하거나, 시연 시 설명이 어긋나기 쉬운 항목 |
| **P1** | UX·관측 가능성(데모 가치)을 높이는 항목 |
| **P2** | 문서/다이어그램 정합성·성능·확장(§5 아이디어 성격) |

---

## TODO 목록 (실행 단위)

### P0 — MCP / 에이전트 도구 정합성

| ID | 상태 | 작업 | 담당 | 산출물·완료 기준 |
|----|------|------|------|------------------|
| **GAP-01** | ✅ (2026-04-06) | `PlayerAgent`의 `bind_tools`에 **`report_to_supervisor`** 추가. LLM이 호출 시 `MCPGameTools.report_to_supervisor` 실행 및 `tool_calls` 파싱 분기. | Cursor | `player_agent.py` + `test_player_agent_report_supervisor.py`. |
| **GAP-02** | ✅ (2026-04-06) | `tool_system_prompt` + `phase_instruction`에 보고 도구 안내·남용 금지 문구 반영. 본문 길이 상한 4000자(도구 실행부). | Cursor | 스팸 시 `state.reports` 길이 상한은 미적용(선택 과제). |

### P1 — 추론·관전 UX (백엔드 + 프론트)

| ID | 상태 | 작업 | 담당 | 산출물·완료 기준 |
|----|------|------|------|------------------|
| **GAP-03** | ✅ (2026-04-06) | AI 턴마다 `internal_notes` 일부를 `agent_thought` WS로 브로드캐스트. `MAFIA_BROADCAST_AGENT_THOUGHTS`·`MAFIA_AGENT_THOUGHT_MAX_CHARS`. | Cursor + Gemini | `events.py`, `runner.py`, `app.py`, `status_panel` expander. |
| **GAP-04** | ✅ (2026-04-06) | `AgentOutput.confidence` + `agent_thought` 페이로드에 선택 포함. **snapshot `players`에는 미포함**(디버그 이벤트만). | Cursor + Gemini | 플레이어 카드 게이지는 미구현(선택). |

### P2 — 다이어그램·문서·관측성 (기획서 외 문서)

| ID | 상태 | 작업 | 담당 | 산출물·완료 기준 |
|----|------|------|------|------------------|
| **GAP-05** | ✅ (2026-04-06) | `TECH_ARCHITECTURE.md` 또는 `AGENT_DESIGN.md`에 실제 진입점 반영: **`apply_action` 없음** → `POST` 핸들러·`GameEngine.submit_*` 직접 호출로 플로우 기술. | Claude 또는 Cursor | `TECH_ARCHITECTURE` v1.3, `AGENT_DESIGN` v1.2. |
| **GAP-06** | ✅ (2026-04-06) | 로그 가시성: RAG 히트 건수 **INFO** 한 줄 + `MAFIA_RAG_LOG_HITS=0` 시 DEBUG만. | Cursor | `retriever.py`, `backend/README.md`. |
| **GAP-07** | ✅ (2026-04-06) | §5 병렬 에이전트: **착수 보류** 및 이유 명시, `TASK_PLAN` **I-19** 백로그 행으로 티켓화. | 기획/Claude | `PROPOSAL` §5 유지 + I-19 참조. |

---

## 권장 실행 순서

1. **GAP-01 → GAP-02** (기획서 MCP 서술과 코드 일치, 시연 시 설명 용이)  
2. **GAP-03** (데모에서 “AI가 왜 그랬는지”를 선택적으로 보여줄 수 있게)  
3. **GAP-05** (신규 합류자·채점자가 아키텍처 문서만 보고도 흐름 이해)  
4. **GAP-06, GAP-07** (리소스·우선순위에 따라 순차 또는 보류) — GAP-04는 `agent_thought`로 충족, 카드 UI는 선택

---

## `TASK_PLAN.md` 연동 제안

다음 스프린트에 반영할 때 이슈 번호 예시:

- **I-17** (또는 다음 빈 번호): GAP-01/GAP-02 — `report_to_supervisor` bind_tools  
- **I-18**: GAP-03 — 관전용 추론 이벤트(선택)

---

## 제출 전 품질 점검 항목 — 역할 범위 (Cursor·에이전트 기준)

아래는 부트캠프 등에서 요구하는 **최종 점검 체크리스트**를, 이 저장소의 **담당 분업**(`.cursorrules` / `CLAUDE.md` / Gemini)과 **Cursor(백엔드) 에이전트가 수행 가능한 범위**만 구분해 둔 것이다.

| 점검 항목 | Cursor(백엔드)에서 **가능** | **부분·협업** | **이 에이전트 단독으로 어려움** |
|-----------|---------------------------|----------------|----------------------------------|
| 프롬프트 vs. 입력 Key 완전 일치 | ✅ 프롬프트 문자열과 `human_prompt`/state 필드 **대조·수정** (`backend/agents/` 등) | 프론트 세션 키와의 정합은 Gemini | — |
| 모든 노드/리턴값 TypedDict·Pydantic 스키마화 | ✅ LangGraph 노드 입출력 **TypedDict/Pydantic 보강** (`graph.py` 등) | 대규모일 때 단계적 PR | — |
| 예외처리·validation 통일성 | ✅ 백엔드 `ValueError`/로그/HTTP detail **패턴 통일** | 프론트 토스트·에러 문구 통일은 Gemini | — |
| 다양한 입력·Live 체크·LangSmith | ✅ **pytest·로컬 실행**으로 회귀 확인, `LANGCHAIN_*` 경로 코드 확인 | `stream`/`batch`/`RunnableParallel` **도입**은 별도 설계·구현 | LangSmith **대시보드에서의 실트레이스 Live 검증**(API 키·브라우저 필요) |
| 문서/체크리스트 제출본 관리 | ✅ `backend/README.md`, 본 `GAP_REMEDIATION_PLAN` 등 **기술 밀접 문서** 보강 | `docs/planning/` 전반 최종 문구는 **Claude(기획)** 우선 | 제출 정책·외부 제출 형식만 정하는 것은 **사용자** |

### 한 줄 요약

- **코드 품질 3종**(키 일치, 스키마화, 예외 통일) → **Cursor(백엔드) 에이전트가 문서화·실행 가능.**
- **LangSmith·RunnableParallel 등 다양한 흐름 Live 검증** → 로컬 테스트·코드 점검은 가능하나, **LangSmith 실사용 Live는 사용자 환경에서 병행** 권장.
- **제출용 docs 전체** → `backend/README`·갭 계획 반영은 가능, **`docs/planning` 일괄 최신화는 기획자와 역할 조율**.

---

## 체크리스트 (복사용)

```
[x] GAP-01  report_to_supervisor → bind_tools + 실행 루프
[x] GAP-02  프롬프트·스팸 방지 가이드
[x] GAP-03  agent_thought WS + 프론트 표시
[x] GAP-04  confidence → agent_thought 페이로드(스냅샷 players 제외)
[x] GAP-05  TECH/AGENT 설계 문서 플로우 수정
[x] GAP-06  RAG 로그 레벨 정책
[x] GAP-07  §5 병렬 실행 등 — 별도 티켓화 여부 결정 (I-19 보류)
```


# 🛠️ 격차 해소 및 최종 보강 계획 (GAP_REMEDIATION_PLAN)

## 1. 개요
최종 과제 제출 전, 프롬프트-코드 간 정합성, 타입 안정성, 예외 처리 통일성 및 테스트 보강을 위한 격차 해소 계획입니다.

## 2. 공통 점검 항목
- [ ] **프롬프트 vs. 입력 Key 완전 일치**: LLM 프롬프트 변수명과 실제 코드 내 상태 전달 값 크로스 체크.
- [ ] **모든 노드/리턴값 TypedDict or Pydantic 스키마화**: 명확한 스키마화(타입 표시) 및 리턴 시 wrapping 여부 체크.
- [ ] **예외처리·validation 통일성**: 일관된 예외 처리 방식(ValueError 등) 및 표준 메시지 포맷 정리.
- [ ] **다양한 입력/테스트 및 LangSmith 트레이싱 적용**: stream/batch/Live 체크 및 디버깅 진행.
- [ ] **문서/체크리스트 제출본 관리**: 제출 문서 최신화 및 미비점 보강.

---

## 3. Gemini (프론트엔드) 작업 세부 내역
> 위 항목 중 프론트엔드 역할 범위에 해당하는 구체적인 작업 항목입니다.

### **[G-18] API Payload Key 및 데이터 모델 정합성 검토**
- [ ] **Key 일치성**: `vote`, `ability`, `chat` 호출 시 전달하는 Key명이 백엔드 Pydantic 모델 및 프롬프트 변수와 일치하는지 전수 검사.
- [ ] **스키마화**: 백엔드 수신 데이터(`game_state_update`)에 대한 프론트엔드 세션 상태(`st.session_state`) 타입 힌트 보강 및 명시적 모델링.

### **[G-19] 예외 처리 및 UI 피드백 통일**
- [ ] **메시지 포맷**: `handle_request_error` 및 `st.toast` 알림의 에러 메시지 형식을 표준화(ex: `[Error] 사유`)하여 사용자 가독성 향상.
- [ ] **안정성**: 네트워크 끊김(WebSocket 연결 해제) 시 재연결 안내 UI 및 초기화 로직 점검.

### **[G-20] 시나리오 테스트 및 제출 문서 최종화**
- [ ] **Live 체크**: 실시간 상태 패널의 RAG/LLM 뱃지 정보가 실제 백엔드 헬스 체크 결과와 일치하는지 실시간 검증.
- [ ] **문서 관리**: `frontend/README.md` 및 `WORK_TASK_GEMINI.md`에 최종 기능 및 디버그 패널 가이드 최신화.
