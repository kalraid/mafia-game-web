import streamlit as st

def draw_lobby():
    st.title("🎭 AI Mafia Online")
    
    player_name = st.text_input("닉네임", placeholder="홍길동")
    player_count = st.slider("총 플레이어 수", min_value=4, max_value=20, value=8)
    
    # 직업 구성 미리보기 (GAME_RULES.md 구성표 기반)
    # 예: 8명 → 마피아2 경찰1 의사1 시민4
    # 이 부분은 추후 구현될 수 있습니다.
    
    if st.button("게임 시작 🎮", disabled=not player_name):
        st.session_state.player_name = player_name
        st.session_state.game_id = f"game_{player_name}_{player_count}"
        st.session_state.player_count = player_count
        st.session_state.page = "game"
        st.rerun()

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

