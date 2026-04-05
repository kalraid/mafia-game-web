import streamlit as st

def draw_lobby():
    st.title("🎭 AI Mafia Online")
    
    player_name = st.text_input("닉네임", placeholder="홍길동")
    player_count = st.slider("총 플레이어 수", min_value=4, max_value=20, value=8)
    
    # 직업 구성 미리보기 로직 (GAME_RULES.md 기반)
    def get_composition(count):
        if count <= 5: return {"마피아": 1, "경찰": 1, "의사": 0, "점쟁이": 0, "시민": count-2}
        if count <= 7: return {"마피아": 1, "경찰": 1, "의사": 1, "점쟁이": 0, "시민": count-3}
        if count <= 9: return {"마피아": 2, "경찰": 1, "의사": 1, "점쟁이": 0, "시민": count-4}
        if count <= 11: return {"마피아": 2, "경찰": 1, "의사": 1, "점쟁이": 0, "시민": count-5, "광대": 1}
        if count <= 14: return {"마피아": 2, "경찰": 1, "의사": 1, "점쟁이": 1, "시민": count-6, "광대": 1}
        if count <= 19: return {"마피아": 2, "킬러": 1, "경찰": 1, "의사": 1, "점쟁이": 1, "시민": count-8, "광대": 1, "스파이": 1}
        return {"마피아": 3, "킬러": 1, "경찰": 2, "의사": 2, "점쟁이": 1, "시민": count-11, "광대": 2, "스파이": 1}

    comp = get_composition(player_count)
    
    with st.expander("📊 예상 직업 구성 확인", expanded=True):
        cols = st.columns(4)
        idx = 0
        icons = {"마피아": "🔫", "킬러": "🗡️", "경찰": "🚓", "의사": "🏥", "점쟁이": "🔮", "시민": "🏙️", "광대": "🎭", "스파이": "🕵️"}
        for role, num in comp.items():
            if num > 0:
                with cols[idx % 4]:
                    st.metric(label=f"{icons.get(role, '')} {role}", value=num)
                idx += 1
    
    if st.button("게임 시작 🎮", disabled=not player_name):
        import requests
        from frontend.utils import handle_request_error
        
        BACKEND_URL = st.session_state.get("BACKEND_URL", "http://localhost:8000")
        
        try:
            resp = requests.post(
                f"{BACKEND_URL}/game/create",
                json={"player_count": player_count, "host_name": player_name},
                timeout=5
            )
            if resp.ok:
                data = resp.json()
                st.session_state.game_id = data.get("game_id")
                st.session_state.player_name = player_name
                st.session_state.player_count = player_count
                st.session_state.page = "game"
                st.rerun()
            else:
                st.error("백엔드에서 게임 생성에 실패했습니다. (API 미구현일 수 있음)")
                # 테스트 환경이나 API 미구현 시 폴백 (선택 사항)
                # st.session_state.game_id = f"game_{player_name}_{player_count}"
                # st.session_state.page = "game"
                # st.rerun()
        except Exception as e:
            st.error(f"서버 연결 오류: {e}")

if __name__ == "__main__":
    # 테스트를 위한 부분
    if 'page' not in st.session_state:
        st.session_state.page = 'lobby'

    if st.session_state.page == 'lobby':
        draw_lobby()
    else:
        st.write(f"게임 '{st.session_state.game_id}' 시작!")
        st.write(f"플레이어: {st.session_state.player_name}")
        st.write(f"총 인원: {st.session_state.player_count}")

