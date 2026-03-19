# 🎨 Gemini 작업 지시서 (WORK_ORDER_GEMINI)

> **대상**: Gemini AI — 프론트엔드 개발자  
> **작성자**: Claude AI (기획자 + 인프라)  
> **최초 작성일**: 2026-03-19  
> **최종 업데이트**: 2026-03-19 (cca37b07 반영)

> 작업 전 반드시 `ROLE_GEMINI.md`와 이 문서를 먼저 읽을 것.  
> **docker-compose.yml은 수정하지 않는다** — Claude 담당.  
> **파일 수정 시 PowerShell/shell 명령어 사용 금지**.

---

## ✅ 완료된 작업

| 항목 | 내용 | 커밋 |
|------|------|------|
| G-2 | 로비 화면 완성 (player_name, game_id, player_count 저장) | `cca37b07` |
| G-3 | 마피아 밤 채팅 채널 탭 분리 (`chat_area.py`) | `cca37b07` |
| G-4 | WebSocket 이벤트 핸들러 (player_death, vote_result, ability_result) | `cca37b07` |
| — | 채팅 phase별 입력창 비활성화 (day_chat만 허용) | `cca37b07` |
| — | 자동 스크롤 JS 추가 | `cca37b07` |
| — | 사망자 메시지 스타일 클래스 적용 | `cca37b07` |

---

## 🔴 긴급 작업 (미완료)

### [G-1] voter/player_name 필드 백엔드 계약 확인

**현황**: `status_panel.py`에서 투표/능력 사용 시 필드명이 백엔드 스펙과 일치하는지 확인 필요.

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

### [G-5] 결과 화면 완성 (`pages/result.py`)

**현황**: 부분 구현됨. 직업 공개·승패 표시 미완성.

**목표**: `game_over` WebSocket 이벤트 payload 기준으로 완성.

**game_over payload 구조**:
```python
{
    "winner": "citizen" | "mafia" | "jester",
    "reason": str,           # 승리 이유 문자열
    "players": [
        {
            "name": str,
            "role": str,         # 한글 직업명
            "is_alive": bool,
            "death_round": int | None,
            "death_cause": str | None,  # "vote" | "mafia" | None
        },
        ...
    ]
}
```

**화면 구성** (`UI_DESIGN.md` §5 기준):
```python
def draw_result():
    game_state = st.session_state.get("game_state", {})
    winner = game_state.get("winner", "unknown")
    reason = game_state.get("reason", "")
    players = game_state.get("players", [])

    # 1. 승리 팀 강조 표시
    winner_text = {"citizen": "🏆 시민 진영 승리!", "mafia": "💀 마피아 승리!", "jester": "🎭 광대 단독 승리!"}
    st.title(winner_text.get(winner, "게임 종료!"))
    st.caption(reason)
    st.divider()

    # 2. 전체 직업 공개 테이블
    st.subheader("최종 직업 공개")
    for p in players:
        status = "✅ 생존" if p.get("is_alive") else f"💀 {p.get('death_round', '?')}라운드 사망"
        cause = p.get("death_cause", "")
        if cause == "vote":
            cause_text = "(투표 처형)"
        elif cause == "mafia":
            cause_text = "(마피아 공격)"
        else:
            cause_text = ""
        st.write(f"**{p['name']}** — {p.get('role', '?')} | {status} {cause_text}")

    st.divider()
    # 3. 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("다시 하기"):
            st.session_state.page = "lobby"
            st.rerun()
```

**참조 문서**: `UI_DESIGN.md` §5 게임 종료 화면

---

## 🟡 중간 우선순위 작업

### [G-6] 낮/밤 테마 CSS 완성 (`assets/style.css`)

**현황**: 기본 낮/밤 클래스 있으나 완성도 확인 필요.

**목표**: Phase에 따라 배경색 + 텍스트 색 자동 전환.

**색상 팔레트** (`UI_DESIGN.md` §7 기준):
```css
/* 낮 테마 */
.day-theme {
    background-color: #FFF8E1;
}

/* 밤 테마 */
.night-theme {
    background-color: #1A1A2E;
    color: #E0E0E0;
}

/* 진영별 */
.mafia-message   { border-left: 3px solid #C0392B; }
.system-message  { background: #F39C12; border-radius: 4px; padding: 4px 8px; }
.my-message      { background: #EBF5FB; }
.other-message   { background: #F2F3F4; }
.dead-message    { opacity: 0.5; text-decoration: line-through; }

/* 사망 오버레이 */
.dead-overlay {
    position: relative;
    pointer-events: none;
}
.dead-overlay::after {
    content: '사망';
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    border-radius: 4px;
}
```

---

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

## ✅ 완료 보고 형식

작업 완료 후 Claude에게 아래 형식으로 보고:

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
