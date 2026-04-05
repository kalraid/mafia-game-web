# 🎨 Gemini 작업 지시서 (WORK_ORDER_GEMINI)

> **대상**: Gemini AI — 프론트엔드 개발자
> **작성자**: Claude AI (기획자 + 인프라 엔지니어)
> **최종 업데이트**: 2026-04-05 (G-13-1~3/G-14 완료 반영, G-13-4 잔존)

> 작업 전 `.geminirules` 읽기 → `WORK_ORDER_GEMINI.md` 확인 → 작업 시작.

---

## 역할 구분

| 항목 | 담당 | 비고 |
|------|------|------|
| `frontend/` | ✅ Gemini | |
| `frontend/Dockerfile` | ✅ Gemini | 완성 |
| `docker-compose.yml` | ❌ Claude | 직접 수정 금지, 필요 시 보고 |

---

## ✅ 완료된 작업 (소스 분석 확인)

| 항목 | 내용 | 확인 |
|------|------|------|
| G-2 | 로비 화면 | ✅ `cca37b07` |
| G-3 | 마피아 채널 탭 | ✅ `cca37b07` |
| G-4 | WebSocket 이벤트 핸들러 | ✅ `cca37b07` |
| G-5 | 결과 화면 | ✅ `82e0600` |
| G-6 | CSS 스타일링 (낮/밤 테마) | ✅ `82e0600` |
| G-8 | frontend/Dockerfile | ✅ `82e0600` |
| G-10 | CSS 경로 버그 (`os.path.join(__file__)` 방식) | ✅ 소스 분석으로 확인 |
| G-11 | REST URL 환경변수화 (`BACKEND_URL`) | ✅ 소스 분석으로 확인 |
| G-7 | `pages/game.py` 레이아웃 (`columns([3,1])`) | ✅ 소스 분석으로 확인 |
| G-9 | `is-suspected-1/2/3` CSS 정의 | ✅ style.css 129~141번 라인 확인 |
| G-1 | voter 필드 확인 | ✅ 소스 분석으로 확인 |
| G-13-1 | `app.py` L78 message 변수 충돌 수정 | ✅ `8fb383e` |
| G-13-2 | `app.py` phase 초기값 "lobby" 수정 | ✅ `c973057` |
| G-13-3 | `status_panel.py` final_speech 투표 버튼 구현 | ✅ `f8d28cf` |
| G-14 | E2E 테스트 셀렉터 3건 수정 | ✅ `9c829fc` |

---

## 🔴 긴급 버그 잔존

### [G-13-4] 즉시 수정 — lobby.py 세션 생성 API 미호출

> **우선순위 최상위** — G-12 이전에 처리.

---

#### G-13-4: `frontend/pages/lobby.py` — 게임 시작 시 백엔드 세션 생성 API 미호출

(내용 기존과 동일 — 아래 참조)

---

## ~~🔴 완료된 긴급 버그~~ ✅ (G-13-1~3, G-14)

### ~~[G-13]~~ 버그 4건 중 3건 완료

---

#### ~~G-13-1~~: `frontend/app.py` L78 — `message` 변수명 충돌 ✅ `8fb383e`

**증상**: `handle_message(message)` 함수 파라미터와 내부 `message = payload.get(...)` 할당 충돌.
`ability_result` 이벤트 처리 시 원본 메시지 객체가 덮어씌워짐.

```python
# 현재 (❌)
def handle_message(message):
    ...
    elif event == "ability_result":
        payload = message.get("payload", {})
        message = payload.get("message", "")   # ← 파라미터 덮어씀

# 수정 (✅)
    elif event == "ability_result":
        payload = message.get("payload", {})
        ability_msg = payload.get("message", "")   # ← 변수명 변경
        st.session_state.ability_result = ability_msg
```

---

#### ~~G-13-2~~: `frontend/app.py` — `game_state` 초기값 phase 불일치 ✅ `c973057`

**증상**: `game_state = {"phase": "day"}` 초기화하나 실제 백엔드 phase 키는 `"day_chat"`, `"day_vote"`, `"night"` 등 → 초기 라우팅 불일치.

```python
# 현재 (❌)
st.session_state.game_state = {"phase": "day"}

# 수정 (✅)
st.session_state.game_state = {"phase": "lobby"}
# phase_map 라우터에 "lobby" 키 없으면 lobby 화면 기본 표시하도록 처리
```

---

#### ~~G-13-3~~: `frontend/components/status_panel.py` — `final_speech` 처형 투표 버튼 미구현 ✅ `f8d28cf`

**증상**: FINAL_VOTE 단계 "처형 찬성 / 반대" 버튼이 `pass`만 있어 동작 불가.

```python
# 현재 (❌)
if st.button("찬성"):
    pass
if st.button("반대"):
    pass

# 수정 (✅)
col1, col2 = st.columns(2)
with col1:
    if st.button("👍 처형 찬성"):
        resp = requests.post(
            f"{BACKEND_URL}/game/{game_id}/vote",
            json={"voter": player_name, "voted_for": st.session_state.get("execution_target")},
        )
        handle_request_error(resp, "투표 실패")
with col2:
    if st.button("👎 처형 반대"):
        resp = requests.post(
            f"{BACKEND_URL}/game/{game_id}/vote",
            json={"voter": player_name, "voted_for": None},
        )
        handle_request_error(resp, "기권 처리 실패")
```

`execution_target`은 `game_state_update` WebSocket payload에서 백엔드가 전달하는 키명으로 연동. 실제 키명은 `backend/game/snapshot.py` 확인 후 맞출 것.

---

#### G-13-4: `frontend/pages/lobby.py` — 게임 시작 시 백엔드 세션 생성 API 미호출

**증상**: "게임 시작" 버튼이 `game_id`를 클라이언트에서만 생성하고 백엔드에 세션 생성 요청을 보내지 않음 → 백엔드 `GameRegistry`에 해당 game_id 없어 WebSocket/API 실패 가능.

```python
# 수정 예시 (백엔드 main.py에서 실제 엔드포인트 확인 후 맞출 것)
if st.button("게임 시작"):
    resp = requests.post(
        f"{BACKEND_URL}/game/create",
        json={"player_count": player_count, "host_name": player_name}
    )
    if resp.ok:
        data = resp.json()
        st.session_state.game_id = data.get("game_id", f"game_{player_name}")
        st.session_state.page = "game"
        st.rerun()
    else:
        st.error("게임 생성 실패")
```

> **주의**: 백엔드에 게임 생성 엔드포인트가 없으면 `[인프라 보고]` 형식으로 Claude에게 보고.

---

### ~~[G-14]~~ ✅ E2E 테스트 셀렉터 수정 완료 (`9c829fc`)

**파일**: `frontend/tests/e2e/test_lobby.py`

분석 결과 셀렉터 3곳이 실제 구현과 불일치해 실행 시 실패 예상.

```python
# BUG-F5: 레이블 불일치
page.get_by_label("내 닉네임:")   # ❌
page.get_by_label("닉네임")       # ✅ (lobby.py st.text_input label)

# BUG-F6: heading 이모지 순서 불일치
name="AI Mafia Online 🎭"         # ❌
name="🎭 AI Mafia Online"         # ✅

# BUG-F7: heading level 불일치 (st.header → h2)
level=1                           # ❌
level=2                           # ✅
```

---

## 🆕 신규 작업 (2026-03-20 추가)

### [G-12] RAG 지식문서 ChromaDB 인덱싱

**배경**: Claude가 `docs/rag_knowledge/` 아래 RAG 지식 문서 20개를 작성 완료.
Cursor(백엔드)가 ChromaDB에 인덱싱하기 전까지, 프론트엔드에서 해당 문서 경로를 참조할 수 있도록 준비.

**파일 구조**:
```
docs/rag_knowledge/
├── strategies/      # mafia_basic, mafia_advanced, citizen_deduction,
│                    # detective_tactics, doctor_protection, jester_tactics, spy_survival
├── speech_patterns/ # aggressive, cautious, logical, emotional, deflection, defense
├── situations/      # early_game, mid_game, endgame_citizen, endgame_mafia,
│                    # ratio_analysis, last_mafia
└── rules/           # game_rules, role_abilities
```

**Gemini 작업 내용**:
1. **RAG 상태 표시 위젯** — `frontend/components/status_panel.py` 또는 사이드바에 추가
   - 현재 게임에서 RAG 검색이 활성화됐는지 여부 표시
   - 백엔드 `/health` 엔드포인트에 RAG 상태 필드가 있다면 연동

2. **디버그 패널 (개발용)** — Streamlit `st.expander("RAG 컨텍스트 보기")` 형태로
   - 게임 상태 업데이트 이벤트에 `rag_context` 필드가 포함되면 표시
   - WebSocket `game_state_update` 이벤트의 payload에 `rag_context` 키가 있으면 펼쳐서 보여주기
   - 없으면 "RAG 컨텍스트 없음" 표시

```python
# 예시 (frontend/components/status_panel.py 또는 game.py)
with st.expander("🔍 RAG 컨텍스트 (디버그)"):
    rag_ctx = game_state.get("rag_context", [])
    if rag_ctx:
        for i, ctx in enumerate(rag_ctx):
            st.markdown(f"**{i+1}.** {ctx}")
    else:
        st.caption("RAG 컨텍스트 없음")
```

**참조**: `docs/rag_knowledge/` 전체, `TECH_ARCHITECTURE.md` §3.3 WebSocket 이벤트

---

## 📢 인프라 보고

```
[인프라 보고] 항목
요청: 환경변수/포트 변경 등
이유: ...
```

## ✅ 완료 보고

```
[완료] G-N — 작업명
구현 내용: ...
설계와 다르게 구현한 부분: ...
Claude에게 요청: ...
```
