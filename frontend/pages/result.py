import streamlit as st

def draw_result():
    st.title("게임 종료!")

    game_state = st.session_state.get("game_state", {})
    winner = game_state.get("winner", "Unknown")
    reason = game_state.get("reason", "The game has ended.")
    players = game_state.get("players", [])

    if winner == "citizen":
        st.header("🏆 시민 진영 승리!")
    elif winner == "mafia":
        st.header("🏆 마피아 진영 승리!")
    else:
        st.header(f"🏆 {winner} 승리!")

    st.write(reason)

    st.markdown("---")
    st.subheader("최종 직업 공개:")

    for player in players:
        role = player.get("role", "Unknown")
        status = "💀" if not player.get("is_alive", True) else "✅"
        st.write(f"{player.get('name', 'Unknown')} → {role} {status}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("다시 하기"):
            # This would ideally reset the game state on the server
            st.session_state.page = "game"
            st.rerun()
    with col2:
        if st.button("로비로 돌아가기"):
            st.session_state.page = "lobby"
            st.rerun()

if __name__ == "__main__":
    st.session_state.game_state = {
        "winner": "citizen",
        "reason": "마피아가 모두 제거되었습니다.",
        "players": [
            {"name": "김민준", "role": "마피아", "is_alive": False},
            {"name": "박서연", "role": "경찰", "is_alive": True},
            {"name": "이지호", "role": "시민", "is_alive": False},
            {"name": "최수아", "role": "의사", "is_alive": True},
        ]
    }
    draw_result()
