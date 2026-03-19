import streamlit as st

def draw_result():
    game_state = st.session_state.get("game_state", {})
    winner = game_state.get("winner", "unknown")
    reason = game_state.get("reason", "")
    players = game_state.get("players", [])

    winner_text = {
        "citizen": "🏆 시민 진영 승리!",
        "mafia": "💀 마피아 승리!",
        "jester": "🎭 광대 단독 승리!"
    }
    st.title(winner_text.get(winner, "게임 종료!"))
    st.caption(reason)
    st.divider()

    st.subheader("최종 직업 공개")
    for p in players:
        status = "✅ 생존" if p.get("is_alive") else f"💀 {p.get('death_round', '?')}라운드 사망"
        cause = p.get("death_cause", "")
        cause_text = {"vote": "(투표 처형)", "mafia": "(마피아 공격)"}.get(cause, "")
        st.write(f"**{p['name']}** — {p.get('role', '?')} | {status} {cause_text}")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("다시 하기"):
            st.session_state.page = "lobby"
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
            {"name": "김민준", "role": "마피아", "is_alive": False, "death_round": 3, "death_cause": "vote"},
            {"name": "박서연", "role": "경찰", "is_alive": True},
            {"name": "이지호", "role": "시민", "is_alive": False, "death_round": 1, "death_cause": "night_attack"},
            {"name": "최수아", "role": "의사", "is_alive": True},
        ]
    }
    draw_result()
