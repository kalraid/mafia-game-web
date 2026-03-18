import streamlit as st
import json
from pages.lobby import draw_lobby
from pages.game import draw_game
from pages.result import draw_result
from streamlit_websocket_client import streamlit_websocket_client

st.set_page_config(layout="wide")

# Load CSS
with open("frontend/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "lobby"
    st.session_state.game_id = "test_game" # Hardcoded for now
    st.session_state.game_state = {"phase": "day"} # Default to day

# WebSocket Connection
ws_url = f"ws://localhost:8000/ws/{st.session_state.game_id}"
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
        elif event == "game_over":
            st.session_state.game_state.update(payload)
            st.session_state.page = "result"
            st.rerun()
        # Add handlers for other events like player_death etc.

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
