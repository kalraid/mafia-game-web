# AI Mafia Online (Backend)

## 요구사항
- Python 3.11+

## 로컬 실행
1. 의존성 설치
   - `pip install -r requirements.txt`
2. 환경변수 준비
   - `.env.example`을 복사해서 `.env`를 만든 뒤 `ANTHROPIC_API_KEY` 등 값을 채워주세요.
3. 서버 실행
   - `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`

## Docker 실행
- `docker-compose up --build`

## WebSocket
- 엔드포인트: `ws://localhost:8000/ws/{game_id}`
- 클라이언트 → 서버 메시지 포맷:
```json
{ "event": "chat_message", "payload": { "content": "hi", "sender": "player" } }
{ "event": "vote", "payload": { "target": "AI_Player_3", "sender": "player" } }
{ "event": "use_ability", "payload": { "target": "AI_Player_5", "ability": "investigate", "sender": "player" } }
```

서버 → 클라이언트 메시지 포맷은 `backend/websocket/events.py`의 `ServerToClientEvent` 계약을 따릅니다.

