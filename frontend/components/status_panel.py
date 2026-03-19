import streamlit as st
import requests
from components.player_card import draw_player_card
from frontend.utils import handle_request_error

def draw_status_panel():
    # Handle selection from query parameters, which is set by clicking a player card
    if "select" in st.query_params:
        selected_player = st.query_params["select"]
        # Toggle selection
        if st.session_state.get("selection") == selected_player:
            st.session_state.selection = None
        else:
            st.session_state.selection = selected_player
        
        # Clear query params to prevent re-triggering on the next rerun
        st.query_params.clear()
        st.rerun()

    st.header("Status")

    
    game_state = st.session_state.get("game_state", {})

    # Phase Display
    phase = game_state.get("phase", "day_chat")
    round_num = game_state.get("round", 0)
    timer_seconds = game_state.get("timer_seconds", 0)

    phase_map = {
        "day_chat": {"icon": "☀️", "text": "낮 토론", "max_time": 180},
        "day_vote": {"icon": "🗳️", "text": "낮 투표", "max_time": 60},
        "final_speech": {"icon": "💬", "text": "최후 변론", "max_time": 30},
        "night": {"icon": "🌙", "text": "밤", "max_time": 90},
        "result": {"icon": "🔔", "text": "결과", "max_time": 10},
        "대기": {"icon": "⏳", "text": "대기", "max_time": 10}
    }
    
    current_phase_info = phase_map.get(phase, {"icon": "❓", "text": phase, "max_time": timer_seconds})
    phase_class = f"phase-{phase}"
    
    timer_js = f"""
    <script>
    // Clear any existing timer to avoid multiple intervals running
    if (window.mafiaTimerInterval) {{
        clearInterval(window.mafiaTimerInterval);
    }}

    function startTimer(duration, display) {{
        let timer = duration;
        window.mafiaTimerInterval = setInterval(function () {{
            let minutes = parseInt(timer / 60, 10);
            let seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;

            display.textContent = minutes + ":" + seconds;

            if (--timer < 0) {{
                clearInterval(window.mafiaTimerInterval);
                // Optionally trigger a rerun when timer ends, though server should do this
            }}
        }}, 1000);
    }}

    // We need to use parent.document because Streamlit runs in an iframe
    const timerDisplay = window.parent.document.querySelector('#mafia-timer-display');
    if (timerDisplay) {{
        startTimer({timer_seconds}, timerDisplay);
    }}
    </script>
    """

    with st.container():
        st.markdown(f"""
            <div class="phase-display {phase_class}">
                <h3>{current_phase_info['icon']} {current_phase_info['text']} {round_num}라운드</h3>
            </div>
            <div class="stMetric">
                <label style="display: block; text-align: center; font-size: 1rem;">남은 시간</label>
                <div data-testid="stMetricValue" style="font-size: 2.25rem; text-align: center;" id="mafia-timer-display">{timer_seconds // 60:02d}:{timer_seconds % 60:02d}</div>
            </div>
            {timer_js}
        """, unsafe_allow_html=True)
        
        max_time = current_phase_info.get("max_time", timer_seconds)
        st.progress(timer_seconds / max_time if max_time > 0 else 0)

    # Player List
    with st.container():
        players = game_state.get("players", [])
        st.subheader(f"플레이어 ({len([p for p in players if p.get('is_alive', False)])}/{len(players)})")
        
        my_name = st.session_state.get("player_name", "")
        phase = game_state.get("phase", "day_chat")
        
        interaction_allowed = phase in ["day_chat", "day_vote", "night"]
        
        if "selection" not in st.session_state:
            st.session_state.selection = None

        if st.session_state.selection:
            st.success(f"현재 선택: **{st.session_state.selection}**")

        for player in players:
            is_me = player.get("name") == my_name
            player_name = player.get("name", "Unknown")
            is_alive = player.get("is_alive", True)
            is_selectable = is_alive and not is_me
            
            draw_player_card(
                player_name=player_name,
                is_alive=is_alive,
                is_me=is_me,
                votes=player.get("votes", 0),
                disabled=not (interaction_allowed and is_selectable),
                role=player.get("role"),
                is_silent=player.get("is_silent", False)
            )

    # Button Area
    with st.container():
        st.subheader("행동")
        phase = game_state.get("phase", "day_chat")
        my_role = st.session_state.get("my_role", "citizen")

        if phase == "day_chat":
            st.write("조사할 플레이어의 채팅을 보려면 카드를 클릭하세요.")
            if st.button("게임 설정"):
                pass
        elif phase == "day_vote":
            st.write("투표할 플레이어를 클릭하세요.")
            if st.button("투표 완료", type="primary"):
                if st.session_state.selection:
                    try:
                        my_name = st.session_state.get("player_name", "UnknownPlayer")
                        game_id = st.session_state.get("game_id", "test_game")
                        target_name = st.session_state.selection
                        
                        response = requests.post(
                            f"http://localhost:8000/game/{game_id}/vote",
                            json={"voter": my_name, "voted_for": target_name}
                        )
                        response.raise_for_status()
                        
                        st.toast(f"✅ {target_name}에게 투표했습니다.", icon="🗳️")
                        st.session_state.selection = None
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "투표 전송 실패")
                else:
                    st.warning("투표할 대상을 먼저 선택해주세요.")

            if st.button("기권(무투표)"):
                try:
                    my_name = st.session_state.get("player_name", "UnknownPlayer")
                    game_id = st.session_state.get("game_id", "test_game")
                    
                    response = requests.post(
                        f"http://localhost:8000/game/{game_id}/vote",
                        json={"voter": my_name, "voted_for": None}
                    )
                    response.raise_for_status()

                    st.toast("✅ 기권했습니다.", icon="🏳️")
                    st.session_state.selection = None
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    handle_request_error(e, "기권 처리 실패")

        elif phase == "final_speech":
             if st.button("처형 찬성"):
                pass
             if st.button("처형 반대"):
                pass
        elif phase == "night":
            my_role = st.session_state.get("my_role", "citizen")
            
            def use_ability(ability_name: str, ability_verb: str):
                if st.session_state.selection:
                    try:
                        my_name = st.session_state.get("player_name", "UnknownPlayer")
                        game_id = st.session_state.get("game_id", "test_game")
                        target_name = st.session_state.selection
                        
                        response = requests.post(
                            f"http://localhost:8000/game/{game_id}/ability",
                            json={"player_name": my_name, "ability": ability_name, "target": target_name}
                        )
                        response.raise_for_status()
                        
                        st.toast(f"✅ {target_name}을(를) {ability_verb} 대상으로 지정했습니다.", icon="🎯")
                        st.session_state.selection = None
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "능력 사용 실패")
                else:
                    st.warning("능력을 사용할 대상을 먼저 선택해주세요.")

            if my_role == "mafia":
                st.write("공격할 대상을 클릭하세요.")
                if st.button("공격 대상 확정", type="primary"):
                    use_ability("attack", "공격")
            elif my_role == "police":
                st.write("조사할 대상을 클릭하세요.")
                if st.button("조사 확정", type="primary"):
                    use_ability("investigate", "조사")
            elif my_role == "doctor":
                st.write("보호할 대상을 클릭하세요.")
                if st.button("보호 확정", type="primary"):
                    use_ability("protect", "보호")
            else:
                st.info("밤이 깊었습니다. 다른 플레이어들의 행동을 기다립니다.")
                st.button("대기 중...", disabled=True)
        else:
            st.write("대기 중...")

if __name__ == "__main__":
    st.session_state.game_state = {
        "phase": "낮", "round": 2, "timer_seconds": 134,
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
