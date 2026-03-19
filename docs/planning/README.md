# AI Mafia Online — 기획 문서 인덱스

> **프로젝트**: AI와 함께하는 웹 마피아 게임  
> **최초 작성일**: 2026-03-18  
> **최종 업데이트**: 2026-03-18

---

## 핵심 기획 문서

| 문서 | 설명 |
|------|------|
| [PRD.md](./PRD.md) | 제품 요구사항 정의서 (전체 개요, 기능 목록, 사용자 원문) |
| [GAME_RULES.md](./GAME_RULES.md) | 마피아 게임 상세 규칙 (직업, 능력, 투표, 승패, 특수 이벤트) |
| [TECH_ARCHITECTURE.md](./TECH_ARCHITECTURE.md) | 기술 아키텍처 (서버 구성, WebSocket, Redis, 데이터 모델) |
| [AGENT_DESIGN.md](./AGENT_DESIGN.md) | AI Agent 설계 (LangGraph, 슈퍼바이저, A2A, RAG, MCP) |
| [UI_DESIGN.md](./UI_DESIGN.md) | UI/UX 화면 설계 (레이아웃, 컴포넌트, 색상 팔레트) |
| [TASK_PLAN.md](./TASK_PLAN.md) | 작업 계획 (Phase별 태스크, 진행 상태, 이슈 목록) |

## 설계 결정 문서

| 문서 | 설명 |
|------|------|
| [RAG_AND_STORAGE_DESIGN.md](./RAG_AND_STORAGE_DESIGN.md) | RAG vs 저장소 설계 결정 (ChromaDB / Redis / In-Memory 분류) |
| [EVALUATION_REFLECTION.md](./EVALUATION_REFLECTION.md) | 평가 피드백 반영 설계 (Agent성, Tool 자율성, 메모리, Structured Output 등) |

## 역할 정의 문서

> ROLE 파일은 프로젝트 루트에 위치합니다.

| 파일 | 위치 | 설명 |
|------|------|------|
| ROLE_CLAUDE.md | 루트 | 클로드 역할 (기획자) — 이 문서를 참조하여 기획자 역할 유지 |
| ROLE_CURSOR.md | 루트 | Cursor 역할 (백엔드/인프라 개발자) |
| ROLE_GEMINI.md | 루트 | Gemini 역할 (프론트엔드 개발자) |

---

## 핵심 기술 스택 요약

| 항목 | 내용 |
|------|------|
| Frontend | Streamlit + WebSocket |
| Backend | FastAPI (단일 서버 권장) |
| AI 프레임워크 | LangChain + LangGraph |
| 에이전트 통신 | MCP (Model Context Protocol) + A2A (Agent-to-Agent) |
| LLM | Claude API (claude-sonnet-4 계열) |
| RAG | ChromaDB + sentence-transformers |
| 세션 메모리 | Redis + LangGraph Checkpointer (필수) |

---

## 현재 진행 상태

```
Phase 0: 환경 구성        ✅ 완료
Phase 1: 게임 엔진        🔄 스캐폴딩 완료
Phase 2: AI Agent         🔄 스캐폴딩 완료
Phase 3: WebSocket + UI   🔄 스캐폴딩 완료
Phase 4: 슈퍼바이저       🔄 스캐폴딩 완료
Phase 5: RAG + MCP        ⬜ 미시작
Phase 6: 통합 테스트      ⬜ 미시작
Phase 7: 배포             🔄 Docker만 완료
```
