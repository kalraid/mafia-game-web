# AI Mafia Online — 기획 문서 인덱스

> **프로젝트**: AI와 함께하는 웹 마피아 게임  
> **최초 작성일**: 2026-03-18

---

## 문서 목록

| 문서 | 설명 |
|------|------|
| [PRD.md](./PRD.md) | 제품 요구사항 정의서 (전체 개요, 기능 목록, 사용자 요구 원문) |
| [GAME_RULES.md](./GAME_RULES.md) | 마피아 게임 상세 규칙 (직업, 능력, 투표, 승패, 특수 이벤트) |
| [TECH_ARCHITECTURE.md](./TECH_ARCHITECTURE.md) | 기술 아키텍처 (서버 구성, WebSocket, 데이터 모델, 의존성) |
| [AGENT_DESIGN.md](./AGENT_DESIGN.md) | AI Agent 설계 (LangGraph, 슈퍼바이저, A2A, RAG, MCP) |
| [UI_DESIGN.md](./UI_DESIGN.md) | UI/UX 화면 설계 (레이아웃, 컴포넌트, 색상 팔레트) |
| [TASK_PLAN.md](./TASK_PLAN.md) | 작업 계획 (Phase별 태스크, 디렉토리 구조, Git 규칙) |

---

## 핵심 기술 스택 요약

- **Frontend**: Streamlit + WebSocket
- **Backend**: FastAPI (단일 서버 권장)
- **AI**: LangChain + LangGraph + RAG (ChromaDB)
- **에이전트 통신**: MCP (Model Context Protocol) + A2A (Agent-to-Agent)
- **LLM**: Claude API (claude-sonnet-4 계열)
