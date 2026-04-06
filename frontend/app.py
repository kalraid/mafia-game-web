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
    st.session_state.game_state = {"phase": "lobby"} # Default to lobby
    st.session_state.BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
    st.session_state.server_connected = False
    st.session_state.rag_status = "unknown"
    
    # On first load, check backend health and RAG status
    try:
        import requests
        response = requests.get(f"{st.session_state.BACKEND_URL}/health", timeout=2)
        if response.status_code == 200:
            st.session_state.server_connected = True
            health_data = response.json()
            # Backend may or may not provide rag_status yet
            st.session_state.rag_status = health_data.get("rag_status", "ok" if "status" in health_data else "unknown")
            st.session_state.llm_provider = health_data.get("llm_provider", "unknown")
        else:
            st.session_state.server_connected = False
            st.session_state.rag_status = "error"
            st.session_state.llm_provider = "unknown"
    except Exception:
        st.session_state.server_connected = False
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
            return True # State changed
        elif event == "chat_broadcast":
            if "chat_history" not in st.session_state.game_state:
                st.session_state.game_state["chat_history"] = []
            st.session_state.game_state["chat_history"].append(payload)
            return True # State changed
        elif event == "player_death":
            dead_player_role = payload.get("role")
            dead_id = payload.get("player_id") or payload.get("player")
            dead_name = payload.get("player")

            if "players" in st.session_state.game_state:
                for p in st.session_state.game_state["players"]:
                    pid = p.get("id", p.get("name"))
                    if dead_id and pid == dead_id:
                        p["is_alive"] = False
                        p["role"] = dead_player_role
                        break
                    if dead_name and p.get("name") == dead_name:
                        p["is_alive"] = False
                        p["role"] = dead_player_role
                        break
            return True # State changed
        elif event == "vote_result":
            # votes_received: target_player_id -> 득표 수 (권장). 없으면 voter->target 맵에서 계산.
            vote_tally = payload.get("votes_received")
            if not vote_tally and isinstance(payload.get("votes"), dict):
                from collections import Counter

                vote_tally = dict(Counter(t for t in payload["votes"].values() if t))
            vote_tally = vote_tally or {}
            if "players" in st.session_state.game_state:
                for p in st.session_state.game_state["players"]:
                    pid = p.get("id", p.get("name"))
                    p["votes"] = int(vote_tally.get(pid, vote_tally.get(p.get("name"), 0)))
            return True # State changed
        elif event == "ability_result":
            payload = data.get("payload", {})
            ability_msg = payload.get("message", "능력 사용 결과가 도착했습니다.")
            success = payload.get("success", True)
            st.session_state.ability_result = ability_msg # Store for potential future use
            if success:
                st.toast(f"✅ {ability_msg}", icon="✅")
            else:
                st.toast(f"❌ {ability_msg}", icon="❌")
            return False # No rerun needed for toast
        elif event == "game_over":
            st.session_state.game_state.update(payload)
            st.session_state.page = "result"
            return True # Page changed
        
        return False

    except json.JSONDecodeError:
        print(f"Could not decode message: {message}")
        return False
    except Exception as e:
        print(f"Error handling message: {e}")
        return False

if messages:
    any_changed = False
    for message in messages:
        if handle_message(message):
            any_changed = True
    
    if any_changed:
        st.rerun()

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
