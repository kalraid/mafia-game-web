import streamlit as st
import json
import os
from pages.lobby import draw_lobby
from pages.game import draw_game
from pages.result import draw_result
from streamlit_websocket_client import streamlit_websocket_client

st.set_page_config(layout="wide")

# Load CSS
# Use a path relative to the current file to be robust against execution context changes.
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "lobby"
    st.session_state.game_id = "test_game" # Hardcoded for now
    st.session_state.game_state = {"phase": "day"} # Default to day
    
    # On first load, check backend health and RAG status
    try:
        import requests
        backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
        response = requests.get(f"{backend_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            st.session_state.rag_status = health_data.get("rag_status", "unknown")
        else:
            st.session_state.rag_status = "error"
    except requests.exceptions.RequestException:
        st.session_state.rag_status = "error"


# WebSocket Connection
# Use environment variable for containerized setup, with a fallback for local dev
ws_base_url = os.environ.get("WS_URL", "ws://localhost:8000")
ws_url = f"{ws_base_url}/ws/{st.session_state.game_id}"
messages = streamlit_websocket_client(url=ws_url)

def handle_message(message):
    try:
        data = json.loads(message)
        event = data.get("event")
        payload = data.get("payload")

        if event == "game_state_update" or event == "phase_change":
            st.session_state.game_state.update(payload)
            st.rerun()
        elif event == "chat_broadcast":
            if "chat_history" not in st.session_state.game_state:
                st.session_state.game_state["chat_history"] = []
            st.session_state.game_state["chat_history"].append(payload)
            st.rerun()
        elif event == "player_death":
            dead_player_name = payload.get("player")
            dead_player_role = payload.get("role")
            
            if "players" in st.session_state.game_state:
                for p in st.session_state.game_state["players"]:
                    if p["name"] == dead_player_name:
                        p["is_alive"] = False
                        p["role"] = dead_player_role # Reveal role on death
                        break
            st.rerun()
        elif event == "vote_result":
            # Payload is expected to be a dict mapping player names to vote counts
            # e.g., {"player1": 2, "player2": 1, "player3": 0}
            vote_counts = payload.get("votes", {})
            if "players" in st.session_state.game_state:
                for p in st.session_state.game_state["players"]:
                    p["votes"] = vote_counts.get(p["name"], 0)
            st.rerun()
        elif event == "ability_result":
            payload = data.get("payload", {})
            ability_msg = payload.get("message", "능력 사용 결과가 도착했습니다.")
            success = payload.get("success", True)
            st.session_state.ability_result = ability_msg # Store for potential future use
            if success:
                st.toast(f"✅ {ability_msg}", icon="✅")
            else:
                st.toast(f"❌ {ability_msg}", icon="❌")
            # No rerun needed for toast
        elif event == "game_over":
            st.session_state.game_state.update(payload)
            st.session_state.page = "result"
            st.rerun()

    except json.JSONDecodeError:
        print(f"Could not decode message: {message}")
    except Exception as e:
        print(f"Error handling message: {e}")

if messages:
    for message in messages:
        handle_message(message)

# Apply theme based on game phase
phase = st.session_state.game_state.get("phase", "day")
theme_class = "night-theme" if phase.lower() == "night" else "day-theme"
st.markdown(f'<script>document.body.className="{theme_class}";</script>', unsafe_allow_html=True)


# Page router
if st.session_state.page == "lobby":
    draw_lobby()
elif st.session_state.page == "game":
    draw_game()
elif st.session_state.page == "result":
    draw_result()
