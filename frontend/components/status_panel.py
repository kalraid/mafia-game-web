import streamlit as st
from components.player_card import draw_player_card

def draw_status_panel():
    st.header("Status")
    
    game_state = st.session_state.get("game_state", {})

    # Phase Display
    phase = game_state.get("phase", "day_chat")
    round_num = game_state.get("round", 0)
    timer = game_state.get("timer_seconds", 0)

    phase_map = {
        "day_chat": {"icon": "☀️", "text": "낮 토론"},
        "day_vote": {"icon": "🗳️", "text": "낮 투표"},
        "final_speech": {"icon": "💬", "text": "최후 변론"},
        "night": {"icon": "🌙", "text": "밤"},
        "result": {"icon": "🔔", "text": "결과"},
        "대기": {"icon": "⏳", "text": "대기"}
    }
    
    current_phase_info = phase_map.get(phase, {"icon": "❓", "text": phase})
    phase_class = f"phase-{phase}"

    with st.container():
        st.markdown(f"""
            <div class="phase-display {phase_class}">
                <h3>{current_phase_info['icon']} {current_phase_info['text']} {round_num}라운드</h3>
            </div>
        """, unsafe_allow_html=True)
        st.metric("남은 시간", f"{timer // 60:02d}:{timer % 60:02d}")
        # Assuming a max time for progress bar, will need to be dynamic later
        st.progress(timer / 180 if timer > 0 else 0)

    # Player List
    with st.container():
        players = game_state.get("players", [])
        st.subheader(f"플레이어 ({len([p for p in players if p.get('is_alive', False)])}/{len(players)})")
        
        my_name = st.session_state.get("player_name", "")

        for player in players:
            is_me = player.get("name") == my_name
            draw_player_card(
                player_name=player.get("name", "Unknown"),
                is_alive=player.get("is_alive", True),
                is_me=is_me,
                votes=player.get("votes", 0)
            )

    # Button Area
    with st.container():
        st.subheader("행동")
        phase = game_state.get("phase", "day_chat") # Default to day_chat for testing
        my_role = st.session_state.get("my_role", "citizen") # Default to citizen

        if phase == "day_chat":
            if st.button("기권하기"):
                pass
            if st.button("게임 설정"):
                pass
        elif phase == "day_vote":
            st.write("투표할 플레이어를 클릭하세요.")
            if st.button("투표 완료"):
                pass
            if st.button("기권(무투표)"):
                pass
        elif phase == "final_speech":
             if st.button("처형 찬성"):
                pass
             if st.button("처형 반대"):
                pass
        elif phase == "night":
            if my_role == "mafia":
                st.write("공격할 대상을 클릭하세요.")
                if st.button("공격 대상 확정"):
                    pass
            elif my_role == "police":
                st.write("조사할 대상을 클릭하세요.")
                if st.button("조사 확정"):
                    pass
            elif my_role == "doctor":
                st.write("보호할 대상을 클릭하세요.")
                if st.button("보호 확정"):
                    pass
            else: # Citizen, Neutrals
                st.button("대기 중...", disabled=True)
        else:
            st.write("대기 중...")


if __name__ == "__main__":
    # Add mock data for testing component in isolation
    st.session_state.game_state = {
        "phase": "낮",
        "round": 2,
        "timer_seconds": 134,
        "players": [
            {"name": "김민준", "is_alive": True},
            {"name": "박서연", "is_alive": True},
            {"name": "이지호", "is_alive": False},
            {"name": "최수아", "is_alive": True},
            {"name": "나", "is_alive": True},
        ]
    }
    st.session_state.player_name = "나"
    draw_status_panel()
