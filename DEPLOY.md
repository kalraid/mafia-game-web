# DEPLOY.md — AI Mafia Online 실행 & 테스트 가이드

> **대상**: 로컬 docker-compose 기반 실행 및 테스트  
> **관리**: Claude AI

---

## 1. 사전 준비

### 필수 설치
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Engine + Compose 포함)
- Git

### ANTHROPIC_API_KEY 확인
- 있으면 → AI 플레이어가 Claude API로 실제 발언/추론
- 없으면 → **Fallback 모드** 동작 (고정 응답, 게임 흐름은 정상 작동)

---

## 2. 최초 설정

```bash
# 1. 저장소 클론 (이미 있으면 생략)
git clone https://github.com/kalraid/mafia-game-web.git
cd mafia-game-web

# 2. 환경변수 파일 생성
cp .env.example .env
```

`.env` 파일을 열어 아래 항목만 편집하면 됩니다:

```env
# AI 기능 사용 시 입력 (없으면 Fallback 모드로 자동 동작)
ANTHROPIC_API_KEY=sk-ant-...

# LLM 비활성화로 빠른 테스트 원할 때
# MAFIA_USE_LLM=0
```

> 나머지 값은 기본값으로 docker-compose와 연동됩니다. 건드리지 않아도 됩니다.

---

## 3. 실행

### 전체 스택 빌드 & 실행

```bash
docker-compose up --build
```

최초 실행 시 이미지 빌드 + 임베딩 모델 다운로드로 수 분 소요됩니다.

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
| **헬스 체크** | http://localhost:8000/health | 서버·RAG 상태 확인 |
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
  "rag_status": "ok"
}
```

| `rag_status` 값 | 의미 |
|----------------|------|
| `ok` | ChromaDB 정상 로드 |
| `unknown` | chromadb 미설치 또는 경로 없음 |
| `error` | 로드 실패 |

---

## 6. 게임 시작 방법

1. http://localhost:8501 접속
2. **닉네임** 입력
3. **인원 수** 선택 (4~20명)
4. **게임 시작** 클릭
   - 백엔드에 세션 자동 생성 (`POST /game/create`)
   - WebSocket 연결 후 AI 플레이어들과 게임 진행

> 인원 수 선택 시 로비에서 역할 구성 미리보기가 표시됩니다.

---

## 7. 테스트

### 백엔드 단위 테스트 (LLM 없이)

```bash
# Docker 없이 로컬에서 실행 (Python 3.11+, requirements.txt 설치 필요)
MAFIA_USE_LLM=0 pytest backend/tests/ -v

# 특정 테스트만
MAFIA_USE_LLM=0 pytest backend/tests/test_game_engine.py -v
MAFIA_USE_LLM=0 pytest backend/tests/test_api_game_create.py -v
MAFIA_USE_LLM=0 pytest backend/tests/test_websocket.py -v
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
POST /game/create       → game_id 발급
POST /game/{id}/chat    → 채팅 전송
POST /game/{id}/vote    → 투표
POST /game/{id}/ability → 능력 사용
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

### RAG rag_status가 unknown

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

### ANTHROPIC_API_KEY 없이 테스트

`.env`에서 `MAFIA_USE_LLM=0` 설정 시 AI 발언이 고정 텍스트로 대체되어 게임 흐름만 테스트 가능합니다.

---

## 10. 원격 서버 배포 시 변경 사항

로컬 → 원격 서버로 옮길 때 `.env` 또는 환경변수만 수정:

```env
# docker-compose.yml 의 environment 섹션 또는 .env 오버라이드
WS_URL=ws://<서버IP>:8000
BACKEND_URL=http://<서버IP>:8000
```

> `docker-compose.yml` 내 `WS_URL`, `BACKEND_URL` 값을 서버 IP로 변경하거나  
> 환경변수로 주입하면 됩니다. Claude에게 문의 후 적용.
