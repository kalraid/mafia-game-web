import streamlit as st

def draw_lobby():
    st.title("AI Mafia Online 🎭")
    
    st.text_input("내 닉네임:", key="player_name")
    
    st.number_input("총 플레이어 수:", min_value=4, max_value=20, value=8, key="total_players")
    
    st.radio("직업 구성:", ("자동", "수동"), key="role_setup")
    
    # Placeholder for estimated role composition
    with st.container():
        st.write("예상 구성:")
        st.info("마피아 2 / 경찰 1 / 의사 1 / 시민 4 / 중립 0")
        
    if st.button("게임 시작 🎮"):
        # Navigate to game page (will be handled in app.py)
        st.session_state.page = "game"
        st.rerun()

if __name__ == "__main__":
    draw_lobby()
