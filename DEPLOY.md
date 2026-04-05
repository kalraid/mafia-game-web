# DEPLOY.md — AI Mafia Online 실행 & 테스트 가이드

> **대상**: 로컬 docker-compose 기반 실행 및 테스트  
> **관리**: Claude AI  
> **최종 업데이트**: 2026-04-05

---

## 1. 사전 준비

### 필수 설치
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Engine + Compose 포함)
- Git

### LLM Provider 선택

이 프로젝트는 **두 가지 LLM Provider**를 지원합니다. 환경변수 하나로 전환합니다.

| Provider | 환경변수 | 용도 |
|---------|---------|------|
| **Anthropic Claude** (기본) | `MAFIA_LLM_PROVIDER=anthropic` | 로컬 개발 |
| **Azure OpenAI** | `MAFIA_LLM_PROVIDER=azure` | 과제 제출 환경 등 |
| **Fallback** (LLM 없음) | `MAFIA_USE_LLM=0` | 빠른 게임 흐름 테스트 |

---

## 2. 최초 설정

```bash
# 1. 저장소 클론 (이미 있으면 생략)
git clone https://github.com/kalraid/mafia-game-web.git
cd mafia-game-web

# 2. 환경변수 파일 생성
cp .env.example .env
```

### 2-A. Anthropic 모드 (기본)

`.env` 파일에서 아래 항목만 입력합니다:

```env
MAFIA_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### 2-B. Azure OpenAI 모드

`.env` 파일에서 아래 항목을 입력합니다:

```env
MAFIA_LLM_PROVIDER=azure

AOAI_ENDPOINT=https://<리소스명>.openai.azure.com/
AOAI_API_KEY=<Azure API 키>
AOAI_API_VERSION=2024-02-01
AOAI_DEPLOY_GPT4O=<GPT-4o 배포명>
AOAI_DEPLOY_GPT4O_MINI=<GPT-4o-mini 배포명>   # 선택
AOAI_DEPLOY_EMBED_3_LARGE=<임베딩 배포명>      # 선택
```

> 나머지 값(`REDIS_URL`, `PORT` 등)은 기본값으로 docker-compose와 자동 연동됩니다.

### 2-C. Fallback 모드 (키 없이 테스트)

```env
MAFIA_USE_LLM=0
```

AI 발언이 고정 텍스트로 대체되어 게임 흐름만 테스트할 수 있습니다.

---

## 3. 실행

### 전체 스택 빌드 & 실행

```bash
docker-compose up --build
```

최초 실행 시 이미지 빌드 + 임베딩 모델 다운로드로 수 분 소요됩니다.

### Provider별 명령어 예시

```bash
# Anthropic 모드 (.env에 설정했거나 직접 주입)
MAFIA_LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... docker-compose up --build

# Azure 모드
MAFIA_LLM_PROVIDER=azure \
AOAI_ENDPOINT=https://my-resource.openai.azure.com/ \
AOAI_API_KEY=xxx \
AOAI_DEPLOY_GPT4O=gpt-4o \
docker-compose up --build

# Fallback 모드 (키 없이 게임 흐름만)
MAFIA_USE_LLM=0 docker-compose up --build
```

### 재실행 (코드 변경 없을 때)

```bash
docker-compose up
```

### 백그라운드 실행

```bash
docker-compose up -d
# 로그 확인
docker-compose logs -f
```

### 종료

```bash
docker-compose down
```

---

## 4. 접속 URL

| 서비스 | URL | 용도 |
|--------|-----|------|
| **프론트엔드** | http://localhost:8501 | 게임 플레이 화면 |
| **백엔드 Swagger** | http://localhost:8000/docs | API 수동 테스트 |
| **헬스 체크** | http://localhost:8000/health | 서버·RAG·LLM 상태 확인 |
| **Redis** | localhost:6379 | 세션/체크포인터 |

---

## 5. 서비스 시작 순서 및 정상 확인

docker-compose가 자동으로 의존 순서를 처리합니다:

```
Redis (healthy) → Backend → Frontend
```

### 정상 기동 로그 예시

```
mafia-redis    | Ready to accept connections
mafia-backend  | INFO:     Uvicorn running on http://0.0.0.0:8000
mafia-frontend | You can now view your Streamlit app in your browser.
```

### 헬스 체크로 상태 확인

```bash
curl http://localhost:8000/health
```

예상 응답:
```json
{
  "status": "ok",
  "rag_status": "ok",
  "llm_provider": "anthropic"
}
```

| 필드 | 값 | 의미 |
|------|----|------|
| `status` | `ok` | 서버 정상 |
| `rag_status` | `ok` | ChromaDB 정상 로드 |
| `rag_status` | `unknown` | chromadb 미설치 또는 경로 없음 |
| `rag_status` | `error` | 로드 실패 |
| `llm_provider` | `anthropic` | Anthropic Claude 활성 |
| `llm_provider` | `azure` | Azure OpenAI 활성 |
| `llm_provider` | `disabled` | `MAFIA_USE_LLM=0` |
| `llm_provider` | `fallback` | Provider 설정됐으나 키 없음 |

프론트엔드 사이드바에서도 현재 LLM provider 상태가 뱃지로 표시됩니다.

---

## 6. 게임 시작 방법

1. http://localhost:8501 접속
2. **닉네임** 입력
3. **인원 수** 선택 (4~20명) — 로비에서 역할 구성 미리보기 표시
4. **게임 시작** 클릭
   - 백엔드에 세션 자동 생성 (`POST /game/create`)
   - WebSocket 연결 후 AI 플레이어들과 게임 진행

---

## 7. 테스트

### 백엔드 단위 테스트 (LLM 없이)

```bash
# Docker 없이 로컬에서 실행 (Python 3.11+, requirements.txt 설치 필요)
MAFIA_USE_LLM=0 pytest backend/tests/ -v

# 주요 테스트 파일
MAFIA_USE_LLM=0 pytest backend/tests/test_game_engine.py -v      # 게임 엔진
MAFIA_USE_LLM=0 pytest backend/tests/test_api_game_create.py -v  # API
MAFIA_USE_LLM=0 pytest backend/tests/test_websocket.py -v        # WebSocket
MAFIA_USE_LLM=0 pytest backend/tests/test_config_llm.py -v       # LLM config
```

### LLM Config 테스트

```bash
# Anthropic 키 설정 후
MAFIA_LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... \
  pytest backend/tests/test_config_llm.py -v

# Azure 키 설정 후
MAFIA_LLM_PROVIDER=azure AOAI_ENDPOINT=... AOAI_API_KEY=... AOAI_DEPLOY_GPT4O=... \
  pytest backend/tests/test_config_llm.py -v
```

### 프론트 단위 테스트

```bash
pytest frontend/tests/pytest/ -v
```

### E2E 테스트 (Playwright)

```bash
# docker-compose 실행 상태에서
pip install playwright pytest-playwright
playwright install chromium

pytest frontend/tests/e2e/ -v
```

### API 수동 테스트 (Swagger UI)

http://localhost:8000/docs 에서 직접 호출 가능:

```
GET  /health                → 서버·RAG·LLM 상태 확인
POST /game/create           → game_id 발급 (player_count: 4~20)
POST /game/{id}/chat        → 채팅 전송
POST /game/{id}/vote        → 투표
POST /game/{id}/ability     → 능력 사용
ws://localhost:8000/ws/{id} → WebSocket 연결
```

---

## 8. 자주 쓰는 명령어

```bash
# 특정 서비스만 재빌드
docker-compose up --build backend

# 백엔드 로그만 보기
docker-compose logs -f backend

# Redis CLI 접속
docker exec -it mafia-redis redis-cli

# 컨테이너 상태 확인
docker-compose ps

# 볼륨 포함 완전 삭제 (ChromaDB 초기화 포함)
docker-compose down -v

# 현재 LLM 상태 확인
curl http://localhost:8000/health | python -m json.tool
```

---

## 9. 트러블슈팅

### 포트 충돌 (8000, 8501, 6379)

```bash
# 사용 중인 포트 확인 (Windows)
netstat -ano | findstr :8000

# .env에서 PORT 변경 가능
PORT=8080
```

### 백엔드가 Redis 연결 실패로 크래시

Redis healthcheck가 통과될 때까지 backend 시작이 지연됩니다.  
이상이 없으면 수 초 후 자동 재시도됩니다.

### `llm_provider: fallback` 으로 표시됨

Provider 설정은 됐으나 API 키가 없는 상태입니다.

```bash
# Anthropic 확인
echo $ANTHROPIC_API_KEY

# Azure 확인
echo $AOAI_API_KEY
echo $AOAI_ENDPOINT
echo $AOAI_DEPLOY_GPT4O
```

`.env` 파일에 해당 값이 올바르게 입력됐는지 확인하세요.

### RAG `rag_status: unknown`

ChromaDB는 첫 게임 완료 후 자동 인덱싱됩니다.  
수동으로 인덱싱하려면:

```bash
docker exec -it mafia-backend python -c "
from backend.rag.store import RAGStore
store = RAGStore()
store.index_knowledge_base('docs/rag_knowledge')
print('인덱싱 완료')
"
```

---

## 10. 원격 서버 배포 시 변경 사항

로컬 → 원격 서버로 옮길 때 아래 값을 서버 IP로 변경합니다.

`docker-compose.yml` 의 frontend environment 섹션:

```yaml
environment:
  - WS_URL=ws://<서버IP>:8000
  - BACKEND_URL=http://<서버IP>:8000
```

또는 환경변수로 직접 주입:

```bash
WS_URL=ws://1.2.3.4:8000 BACKEND_URL=http://1.2.3.4:8000 docker-compose up -d
```

> `docker-compose.yml` 수정은 Claude 담당입니다. 변경이 필요하면 요청해 주세요.
