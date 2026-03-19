# 🎨 Gemini 작업 지시서 (WORK_ORDER_GEMINI)

> **대상**: Gemini AI — 프론트엔드 담당  
> **작성자**: Claude AI (기획자)  
> **최초 작성일**: 2026-03-19  
> **기준 커밋**: `978c755`

> 작업 전 반드시 `ROLE_GEMINI.md`와 이 문서를 먼저 읽을 것.

---

## 현재 구현 상태 (기준점)

프론트엔드 초안 커밋(`6a6086d`) 기준으로 아래가 이미 구현되어 있음:
- `status_panel.py`: Phase별 버튼 + 타이머 JS ✅
- `player_card.py`: 투표 수, 사망 오버레이, 클릭 선택 ✅
- `chat_area.py`: 채팅 표시 ✅ (검토 필요)
- `frontend/utils.py`: `handle_request_error()` ✅
- REST 방식 투표/능력 (`requests.post`) ✅

---

## 🔴 긴급 작업

### [G-1] voter_id 필드 통일 (백엔드와 계약 확정)

**현황**: 백엔드 `/game/{id}/vote` API가 `voter` 필드를 받는데, 프론트에서 `player_name`으로 보내는 부분이 혼재할 가능성 있음.

**목표**: 전송 필드명 통일.

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

### [G-2] 로비 화면 완성

**현황**: `pages/lobby.py` 내용 미확인. 게임 시작 시 player_name, game_id, player_count가 session_state에 제대로 저장되어야 함.

**목표**: 로비에서 닉네임 + 인원 수 입력 → 게임 시작 → session_state 저장.

**구체적 작업**:
```python
# pages/lobby.py
def draw_lobby():
    st.title("🎭 AI Mafia Online")
    
    player_name = st.text_input("닉네임", placeholder="홍길동")
    player_count = st.slider("총 플레이어 수", min_value=4, max_value=20, value=8)
    
    # 직업 구성 미리보기 (GAME_RULES.md 구성표 기반)
    # 예: 8명 → 마피아2 경찰1 의사1 시민4
    
    if st.button("게임 시작 🎮", disabled=not player_name):
        st.session_state.player_name = player_name
        st.session_state.game_id = f"game_{player_name}_{player_count}"
        st.session_state.player_count = player_count
        st.session_state.page = "game"
        st.rerun()
```

**참조 문서**: `UI_DESIGN.md` §4 로비 화면, `GAME_RULES.md` §1.1 인원 구성표

---

### [G-3] 마피아 밤 채팅 채널 분리 UI 반영

**현황**: 채팅창이 `global` 채널만 표시. 밤에 마피아는 `mafia_secret` 채널 채팅을 별도로 볼 수 있어야 함.

**목표**: 밤 Phase + 마피아 역할일 때 채팅창에 마피아 비밀 채널 탭 or 별도 표시.

**구체적 작업**:
```python
# chat_area.py
def draw_chat_area():
    phase = st.session_state.game_state.get("phase", "day_chat")
    my_role = st.session_state.get("my_role", "citizen")
    chat_history = st.session_state.game_state.get("chat_history", [])
    
    is_night = "night" in phase
    is_mafia = my_role in ["mafia", "killer"]
    
    if is_night and is_mafia:
        # 탭으로 채널 분리
        tab_global, tab_mafia = st.tabs(["전체 채팅", "🔴 마피아 비밀 채널"])
        with tab_mafia:
            mafia_chats = [m for m in chat_history if m.get("channel") == "mafia_secret"]
            # 마피아 채팅 표시
    else:
        # 일반 채팅만
        global_chats = [m for m in chat_history if m.get("channel") in ["global", "system"]]
```

**참조 문서**: `UI_DESIGN.md` §2.3 채팅 동작 규칙, `TECH_ARCHITECTURE.md` §3.2 채널 분리

---

## 🟡 중간 우선순위 작업

### [G-4] 게임 화면 WebSocket 이벤트 수신 안정화

**현황**: `frontend/app.py`에서 WebSocket 메시지를 받아 처리하고 있으나, `player_death` 이벤트 처리 미확인.

**목표**: 모든 서버 이벤트를 빠짐없이 처리.

**이벤트별 처리 목록** (서버 → 클라이언트):

| 이벤트 | 처리 내용 |
|--------|----------|
| `chat_broadcast` | chat_history에 추가 |
| `phase_change` | game_state.phase 업데이트 + 테마 전환 |
| `game_state_update` | 전체 game_state 갱신 |
| `player_death` | 해당 플레이어 is_alive=False + 사망 오버레이 |
| `vote_result` | 플레이어 votes 수 업데이트 |
| `ability_result` | 성공/실패 토스트 메시지 |
| `game_over` | result 페이지로 이동 |

---

### [G-5] 결과 화면 완성

**현황**: `pages/result.py` 부분 업데이트됨. 직업 공개, 승패 표시 완성도 확인 필요.

**목표**: 게임 종료 시 전체 직업 공개 + 승패 결과 표시.

**표시 내용** (`game_over` payload 기준):
```python
# winner: "citizen" | "mafia" | "jester"
# players: [{ name, role, is_alive, death_round, death_cause }]

# 승리 팀 강조
# 전체 직업 공개 테이블
# 다시 하기 / 로비로 버튼
```

**참조 문서**: `UI_DESIGN.md` §5 게임 종료 화면

---

### [G-6] 낮/밤 테마 전환 CSS 완성

**현황**: `style.css`에 기본 낮/밤 클래스 있으나 완성도 확인 필요.

**목표**: Phase에 따라 배경색 + 텍스트 색 자동 전환.

**색상 팔레트** (`UI_DESIGN.md` §7 기준):
```css
/* 낮 테마 */
.day-theme { background: #FFF8E1; }

/* 밤 테마 */
.night-theme { background: #1A1A2E; color: #E0E0E0; }

/* 사망 오버레이 */
.dead-overlay {
    position: relative;
}
.dead-overlay::after {
    content: '사망';
    position: absolute;
    background: rgba(0, 0, 0, 0.75);
    /* 전체 카드 덮기 */
}
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
