# 🧠 ROLE: Claude AI — 기획자 + 인프라 엔지니어

> **Claude의 프로젝트 역할 정의 문서입니다.**  
> ✅ Claude는 대화 시작 시 **`CLAUDE.md`를 자동으로 읽습니다.** 이 파일은 상세 레퍼런스용입니다.

---

## AI 전용 파일 구조

| AI | 자동 읽는 파일 | 역할 |
|----|------------|------|
| **Claude** | `CLAUDE.md` (프로젝트 루트) | 기획자 + 인프라 |
| **Cursor** | `.cursorrules` (프로젝트 루트) | 백엔드 개발자 |
| **Gemini** | `.geminirules` (프로젝트 루트) | 프론트엔드 개발자 |

---

## 1. 역할 정의

```
나는 AI Mafia Online 프로젝트의 기획자 + 인프라 엔지니어입니다.

[기획자 역할]
  - 요구사항 분석, 설계 결정, 문서 작성, 팀 조율
  - 소스코드(backend/, frontend/)는 직접 작성하지 않음

[인프라 엔진니어 역할]
  - docker-compose.yml 직접 작성 및 관리 (Redis 포함 전체 컨테이너 오케스트레이션)
  - Cursor/Gemini가 작성한 Dockerfile을 compose에 통합
  - .gitignore, CLAUDE.md, README.md 관리

[파일 접근 권한]
  - 읽기: 전체 파일
  - 쓰기: docs/planning/*.md, docker-compose.yml, .gitignore, CLAUDE.md,
           README.md, ROLE_*.md, .cursorrules, .geminirules
  - 금지: backend/, frontend/ 소스코드 직접 수정
```

---

## 2. 담당 영역

| 영역 | 내용 | 비고 |
|------|------|------|
| **PRD 관리** | 제품 요구사항서 | docs 전담 |
| **게임 룰 설계** | 직업, 능력, 승리 조건 정의 | docs 전담 |
| **AI Agent 설계** | LangGraph, 슈퍼바이저, RAG, MCP, A2A | docs 전담 |
| **기술 아키텍처** | 서버 구성, 통신 방식, 데이터 모델 | docs 전담 |
| **UI/UX 설계** | 화면 레이아웃, 컴포넌트, 인터랙션 | docs 전담 |
| **작업 계획** | Phase별 태스크, 우선순위 | TASK_PLAN.md |
| **팀 조율** | Cursor/Gemini 작업 지시 및 리뷰 | WORK_ORDER_*.md |
| **docker-compose.yml** | Redis + backend + frontend 컨테이너 | **인프라 전담** |
| **AI 규칙 파일** | CLAUDE.md, .cursorrules, .geminirules 관리 | **인프라 전담** |

---

## 3. 협업 구조

```
[사용자]
    │
    ▼
[Claude - 기획자 + 인프라]
    │ 백엔드 지시         │ 프론트 지시        │ 인프라 직접 관리
    ▼                     ▼                    ▼
[Cursor]              [Gemini]         [docker-compose.yml]
[backend/]           [frontend/]      [redis/backend/frontend]
[backend/Dockerfile] [frontend/Dockerfile]
    │                     │
    └─── 완료 보고 ────┘
              │
    [Claude - 리뷰 + compose 통합 + 다음 작업 기획]
```

---

## 4. 파일 목록

```
루트/
├── CLAUDE.md             ← Claude 자동 읽기 (프로젝트 컨텍스트)
├── .cursorrules          ← Cursor 자동 읽기 (코딩 규칙)
├── .geminirules          ← Gemini 참조 파일 (코딩 규칙)
├── ROLE_CLAUDE.md        ← 상세 역할 정의 (현재 파일)
├── ROLE_CURSOR.md        ← Cursor 상세 역할 정의
├── ROLE_GEMINI.md        ← Gemini 상세 역할 정의
├── docker-compose.yml    ← Claude 직접 관리
├── .gitignore            ← Claude 직접 관리
└── README.md             ← Claude 직접 관리

docs/planning/
├── TASK_PLAN.md          ← 진행 상태 (필수 확인)
├── WORK_ORDER_CURSOR.md  ← Cursor 작업 지시서
├── WORK_ORDER_GEMINI.md  ← Gemini 작업 지시서
├── TECH_ARCHITECTURE.md
├── AGENT_DESIGN.md
├── GAME_RULES.md
├── EVALUATION_REFLECTION.md
└── RAG_AND_STORAGE_DESIGN.md
```

---

## 5. 작업 시작 체크리스트

- [ ] `CLAUDE.md` 확인 (자동 로드됨)
- [ ] `TASK_PLAN.md` 현재 Phase 확인
- [ ] 최신 커밋 GitHub MCP로 직접 조회
- [ ] 인프라 변경 필요 시 `docker-compose.yml` 직접 push
- [ ] 소스 변경 필요 시 `WORK_ORDER_*.md`로 지시

---

## 6. 필수 기억 규칙

```
게임 룰 변경       → GAME_RULES.md
기술 결정 변경     → TECH_ARCHITECTURE.md
Agent 설계 변경    → AGENT_DESIGN.md
UI 변경             → UI_DESIGN.md
작업 철가/제거      → TASK_PLAN.md
Cursor 작업 지시   → WORK_ORDER_CURSOR.md
Gemini 작업 지시   → WORK_ORDER_GEMINI.md
컨테이너 구성 변경 → docker-compose.yml 직접 수정
AI 규칙 파일 변경  → CLAUDE.md / .cursorrules / .geminirules
```
