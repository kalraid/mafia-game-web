# 🎨 Gemini 작업 지시서 (WORK_ORDER_GEMINI)

> **대상**: Gemini AI — 프론트엔드 개발자  
> **작성자**: Claude AI (기획자 + 인프라 엔지니어)  
> **최종 업데이트**: 2026-03-19 (docker-compose 테스트 분석 반영)

> 작업 전 `.geminirules` 읽기 → `WORK_ORDER_GEMINI.md` 확인 → 작업 시작.

---

## 역할 구분

| 항목 | 담당 | 비고 |
|------|------|------|
| `frontend/` | ✅ Gemini | |
| `frontend/Dockerfile` | ✅ Gemini | 완성 |
| `docker-compose.yml` | ❌ Claude | 직접 수정 금지, 필요 시 보고 |

---

## ✅ 완료된 작업

| 항목 | 커밋 |
|------|------|
| G-2 로비 화면 | `cca37b07` |
| G-3 마피아 채널 탭 | `cca37b07` |
| G-4 WebSocket 이벤트 핸들러 | `cca37b07` |
| G-5 결과 화면 | `82e0600` |
| G-6 CSS 스타일링 (낮/밤 테마) | `82e0600` |
| G-8 frontend/Dockerfile | `82e0600` |

---

## 🔴 긴급 작업 (마지 막는 중)

### [G-10] CSS 경로 버그 수정 — **docker-compose 크래시 원인**

**파일**: `frontend/app.py`  
**원인**: 컨테이너 WORKDIR는 `/app`, 파일은 `COPY . .`로
`/app/assets/style.css` 위치에 있으나 코드는 `frontend/assets/style.css`를 찾아 **FileNotFoundError** 만발.

```python
# 현재 (❌ 컨테이너에서 컨테이너 크래시)
with open("frontend/assets/style.css") as f:
    st.markdown(...)

# 수정 (✅ 컨테이너 + 로컀 모두 동작)
import os
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
```

> **주의**: `os.path.dirname(__file__)` 사용 시 로컀(`streamlit run frontend/app.py`)와
> 컨테이너(`streamlit run app.py`) 모두 에서 정확한 경로를 찾습니다.

---

### [G-11] REST API URL 환경변수화

**파일**: `frontend/components/status_panel.py`  
**문제**: REST 호출이 `http://localhost:8000` 하드코딩. 서버 배포 시 호스트명 변경 시 일일이 수정 필요.

```python
# 현재 (❌ 하드코딩)
requests.post(f"http://localhost:8000/game/{game_id}/vote", ...)

# 수정 (✅ 환경변수 활용)
import os
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
requests.post(f"{BACKEND_URL}/game/{game_id}/vote", ...)
```

적용 대상: `status_panel.py`의 **모든** `requests.post` 호출 (vote, ability)

---

## 🟡 중간 우선순위

### [G-1] voter 필드 확인

`status_panel.py`에서 투표/능력 Body의 키 이름이 스펙 일치하는지 확인:
```
POST /vote:    { "voter": str, "voted_for": str | None }
POST /ability: { "player_name": str, "ability": str, "target": str }
```

### [G-7] `pages/game.py` 레이아웃

3/4 채팅 + 1/4 상태창 확인:
```python
def draw_game():
    col_chat, col_status = st.columns([3, 1])
    with col_chat:   draw_chat_area()
    with col_status: draw_status_panel()
```

### [G-9] `is-suspected-N` CSS

`player_card.py`에서 `is-suspected-1/2/3` 클래스 적용 중이나 `style.css`에 정의 없음.  
**방법 A**: style.css에 추가  
**방법 B**: player_card.py에서 해당 로직 제거

---

## 📢 인프라 보고

```
[인프라 보고] 항목매
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
