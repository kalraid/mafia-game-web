# 🎨 Gemini 작업 지시서 (WORK_ORDER_GEMINI)

> **대상**: Gemini AI — 프론트엔드 담당  
> **작성자**: Claude AI (기획자)  
> **최초 작성일**: 2026-03-19  
> **최종 업데이트**: 2026-03-19 (cca37b07 반영)

> 작업 전 반드시 `ROLE_GEMINI.md`와 이 문서를 먼저 읽을 것.

---

## 완료된 작업 ✅

| 항목 | 내용 | 커밋 |
|------|------|------|
| G-2 | 로비 화면 완성 | `cca37b07` |
| G-3 | 마피아 밤 채팅 채널 탭 분리 UI | `cca37b07` |
| G-4 | WebSocket 이벤트 수신 (player_death, vote_result, ability_result) | `cca37b07` |
| 채팅 phase 제한 | day_chat 이외 입력창 비활성화 | `cca37b07` |
| 자동 스크롤 | 신규 메시지 도착 시 최하단 이동 JS | `cca37b07` |
| 사망자 메시지 스타일 | dead-message 클래스 적용 | `cca37b07` |

---

## 🔴 긴급 작업 (미완료)

### [G-1] voter_id 필드 통일 확인

**현황**: `status_panel.py`에서 투표 시 `voter` 키를 사용하는데 실제 `app.py`의 session_state에서 player_name이 올바르게 전달되는지 확인 필요.

**확인 및 수정**:
```python
# status_panel.py 투표 전송 부분
response = requests.post(
    f"http://localhost:8000/game/{game_id}/vote",
    json={
        "voter": my_name,        # ← 반드시 "voter" 키 사용
        "voted_for": target_name
    }
)

# 능력 사용 전송 부분
response = requests.post(
    f"http://localhost:8000/game/{game_id}/ability",
    json={
        "player_name": my_name,  # ← 반드시 "player_name" 키 사용
        "ability": ability_name,
        "target": target_name
    }
)
```

**백엔드 API 스펙** (`main.py` 기준):
```
POST /game/{game_id}/vote    → { voter: str, voted_for: str | None }
POST /game/{game_id}/ability → { player_name: str, ability: str, target: str }
POST /game/{game_id}/chat    → { sender: str, content: str, channel: str }
```

---

## 🟡 중간 우선순위 작업

### [G-5] 결과 화면 완성

**현황**: `pages/result.py` 부분 업데이트됨. 직업 공개·승패 표시 완성도 확인 필요.

**목표**: `game_over` WebSocket 이벤트 payload 기준으로 완성.

**표시 내용** (`game_over` payload 기준):
```python
# winner: "citizen" | "mafia" | "jester"
# reason: 승리 이유 문자열
# players: [{ name, role, is_alive, death_round, death_cause }]

# 화면 구성:
# 1. 승리 팀 강조 (🏆 시민 진영 승리! 등)
# 2. 전체 직업 공개 테이블
# 3. 다시 하기 / 로비로 버튼
```

**참조 문서**: `UI_DESIGN.md` §5 게임 종료 화면

---

### [G-6] 낮/밤 테마 CSS 완성

**현황**: `style.css`에 기본 낮/밤 클래스 있으나 완성도 확인 필요.

**목표**: Phase에 따라 배경색 + 텍스트 색 자동 전환.

**색상 팔레트** (`UI_DESIGN.md` §7 기준):
```css
/* 낮 테마 */
.day-theme { background: #FFF8E1; }

/* 밤 테마 */
.night-theme { background: #1A1A2E; color: #E0E0E0; }

/* 진영별 */
--color-citizen: #2980B9;
--color-mafia:   #C0392B;
--color-neutral: #8E44AD;

/* 사망 오버레이 */
.dead-overlay::after {
    content: '사망';
    position: absolute;
    background: rgba(0, 0, 0, 0.75);
}
```

---

### [G-7] 게임 화면 (`pages/game.py`) 내용 확인

**현황**: `pages/game.py` 내용 미확인. 3/4 채팅 + 1/4 상태창 레이아웃이 설계대로 구현됐는지 검토 필요.

**목표**: `UI_DESIGN.md` §1 레이아웃 기준 충족 확인.

```python
# 기대 구조
def draw_game():
    col_chat, col_status = st.columns([3, 1])  # 3/4 : 1/4
    with col_chat:
        draw_chat_area()
    with col_status:
        draw_status_panel()
```

---

## ✅ 완료 보고 형식

작업 완료 후 Claude에게 아래 형식으로 보고:

```
[완료] G-N — 작업명

구현 내용:
- ...

백엔드(Cursor)에 요청 필요한 사항:
- ...

설계와 다르게 구현한 부분:
- ...
```

---

## 📋 참조 문서 목록

| 문서 | 참조 이유 |
|------|----------|
| `UI_DESIGN.md` | 화면 레이아웃, 컴포넌트, 색상, Phase별 버튼 |
| `TECH_ARCHITECTURE.md` | WebSocket 이벤트 계약, REST API 스펙 |
| `GAME_RULES.md` | 인원 구성표 (로비 미리보기), Phase 흐름 |
