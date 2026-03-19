# 🎨 Gemini 작업 지시서 (WORK_ORDER_GEMINI)

> **대상**: Gemini AI — 프론트엔드 개발자  
> **작성자**: Claude AI (기획자 + 인프라 엔지니어)  
> **최초 작성일**: 2026-03-19  
> **최종 업데이트**: 2026-03-19 (82e0600 반영)

> 작업 전 반드시 `ROLE_GEMINI.md`와 이 문서를 먼저 읽을 것.  
> **docker-compose.yml은 수정하지 않는다** — Claude 담당, 필요 사항은 보고.

---

## 역할 구분 (필수 숙지)

| 항목 | 담당 | 비고 |
|------|------|------|
| `frontend/` 소스코드 | ✅ Gemini | |
| `frontend/Dockerfile` | ✅ Gemini | 완성 후 Claude에게 보고 → compose 통합 |
| `docker-compose.yml` | ❌ Claude | **수정 금지** — 필요사항은 보고 |
| `docs/planning/` | ❌ Claude | **수정 금지** |
| `backend/` | ❌ Cursor | |

---

## ✅ 완료된 작업

| 항목 | 내용 | 커밋 |
|------|------|------|
| G-2 | 로비 화면 완성 (player_name, game_id, player_count 저장) | `cca37b07` |
| G-3 | 마피아 밤 채팅 채널 탭 분리 (`chat_area.py`) | `cca37b07` |
| G-4 | WebSocket 이벤트 핸들러 (player_death, vote_result, ability_result) | `cca37b07` |
| G-5 | 결과 화면 완성 (winner/직업공개/사망정보/버튼) | `82e0600` |
| G-6 | CSS 스타일링 완성 (낮/밤 테마, 채팅 스타일, dead-overlay) | `82e0600` |
| G-8 | frontend/Dockerfile 완성 → docker-compose 통합 완료 | `82e0600` |
| — | frontend/requirements.txt 신규 (프론트 전용 의존성 분리) | `82e0600` |
| — | app.py WS_URL 환경변수 지원 추가 (컨테이너화 대응) | `82e0600` |

---

## 🔴 긴급 작업 (미완료)

### [G-1] voter/player_name 필드 백엔드 계약 확인

**현황**: `status_panel.py`에서 투표/능력 사용 시 필드명이 백엔드 스펙과 일치하는지 명시적 확인 미완료.

**백엔드 API 스펙** (`TECH_ARCHITECTURE.md` 기준):
```python
# 투표
POST /game/{game_id}/vote
Body: { "voter": str, "voted_for": str | None }

# 능력 사용
POST /game/{game_id}/ability
Body: { "player_name": str, "ability": str, "target": str }
# ※ ability값 "protect" → 서버에서 자동으로 "heal"로 변환
```

**확인 및 수정**:
```python
# status_panel.py 투표 전송 부분
response = requests.post(
    f"http://localhost:8000/game/{game_id}/vote",
    json={"voter": my_name, "voted_for": target_name}  # ← "voter" 키 확인
)

# 능력 사용 전송 부분
response = requests.post(
    f"http://localhost:8000/game/{game_id}/ability",
    json={"player_name": my_name, "ability": ability_name, "target": target_name}  # ← "player_name" 키 확인
)
```

---

## 🟡 중간 우선순위 작업

### [G-7] 게임 화면 (`pages/game.py`) 레이아웃 확인

**현황**: `pages/game.py` 내용 미확인. 3/4 + 1/4 컬럼 레이아웃이 설계대로인지 확인 필요.

**기대 구조**:
```python
def draw_game():
    col_chat, col_status = st.columns([3, 1])  # 3/4 : 1/4
    with col_chat:
        from components.chat_area import draw_chat_area
        draw_chat_area()
    with col_status:
        from components.status_panel import draw_status_panel
        draw_status_panel()
```

**참조 문서**: `UI_DESIGN.md` §1 화면 구성 개요

---

### [G-9] `is-suspected-N` CSS 클래스 정리 (마이너)

**현황**: `player_card.py`에서 `is-suspected-1`, `is-suspected-2`, `is-suspected-3` 클래스를 votes 수에 따라 적용하고 있으나 `style.css`에 해당 클래스 정의가 없음 → 시각적 효과 없음.

**선택지**: 아래 중 하나 선택 후 적용.
```css
/* 방법 A: style.css에 추가 */
.is-suspected-1 { border: 1px solid #E67E22; }
.is-suspected-2 { border: 2px solid #E74C3C; }
.is-suspected-3 { border: 3px solid #C0392B; background: #FDEDEC; }

/* 방법 B: player_card.py에서 해당 로직 제거 */
# votes > 0 블록 삭제
```

---

## 📢 인프라 보고 방법

docker-compose.yml 변경이 필요한 사항이 생기면 **직접 수정하지 말고** Claude에게 보고:

```
[인프라 보고] 항목명

요청 내용:
  - 새로운 환경변수: FOO=bar
  - 포트 노출 변경: 8501
  - 기타: ...

이유:
  - ...
```

---

## ✅ 완료 보고 형식

```
[완료] G-N — 작업명

구현 내용:
- ...

설계와 다르게 구현한 부분 (있을 경우):
- ...

Claude에게 요청 필요한 사항 (docker-compose, docs 변경 등):
- ...
```

---

## 📋 참조 문서 목록

| 문서 | 참조 이유 |
|------|----------|
| `UI_DESIGN.md` | 화면 레이아웃, 컴포넌트, 색상 팔레트 |
| `TECH_ARCHITECTURE.md` | WebSocket 이벤트 계약, REST API 스펙 |
| `GAME_RULES.md` | 인원 구성표 (로비 미리보기), Phase 흐름 |
