import streamlit as st
import requests
import os
from datetime import datetime
from frontend.utils import handle_request_error

# Use environment variable for containerized setup, with a fallback for local dev
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

def _draw_message(msg, my_name, dead_players, highlight_player, phase):
    sender = msg.get("sender", "System")
    content = msg.get("content", "")
    channel = msg.get("channel", "global")
    timestamp = msg.get("timestamp", datetime.now().strftime("%H:%M"))

    class_list = ["chat-message"]
    
    # In the new G-6 CSS, the message header is gone, so this logic is simplified.
    # We still use the classes to apply different background colors.
    is_dead_sender = sender in dead_players
    if is_dead_sender:
        class_list.append("dead-message")

    if sender == "System":
        class_list.append("system-message")
    elif sender == my_name:
        class_list.append("my-message")
    elif channel == "mafia_secret":
        class_list.append("mafia-message")
    else:
        class_list.append("other-message")

    st.markdown(f'<div class="{" ".join(class_list)}">{content}</div>', unsafe_allow_html=True)


def draw_chat_area():
    st.header("Chat")

    game_state = st.session_state.get("game_state", {})
    chat_history = game_state.get("chat_history", [])
    players = game_state.get("players", [])
    my_name = st.session_state.get("player_name", "Player")
    game_id = st.session_state.get("game_id", "test_game")
    my_role = st.session_state.get("my_role", "citizen")
    
    phase = game_state.get("phase", "day_chat")
    highlight_player = st.session_state.get("selection")

    dead_players = {p["name"] for p in players if not p.get("is_alive", True)}
    
    is_night = "night" in phase
    is_mafia = my_role in ["mafia", "killer"]

    def render_chat_list(messages):
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in messages:
            # The new G-6 CSS simplifies message structure, so we adapt the call
            _draw_message(msg, my_name, dead_players, highlight_player, phase)
        st.markdown('</div>', unsafe_allow_html=True)
        # JS for auto-scrolling
        st.markdown("""
            <script>
                const chatContainers = window.parent.document.querySelectorAll('.chat-container');
                if (chatContainers.length > 0) {
                    const lastChatContainer = chatContainers[chatContainers.length - 1];
                    lastChatContainer.scrollTop = lastChatContainer.scrollHeight;
                }
            </script>
        """, unsafe_allow_html=True)

    if is_night and is_mafia:
        tab_global, tab_mafia = st.tabs(["전체 채팅", "🔴 마피아 비밀 채널"])
        
        with tab_global:
            global_chats = [m for m in chat_history if m.get("channel") in ["global", "system"]]
            render_chat_list(global_chats)
            
        with tab_mafia:
            mafia_chats = [m for m in chat_history if m.get("channel") == "mafia_secret"]
            render_chat_list(mafia_chats)

            # Mafia chat input
            mafia_chat_input = st.text_input("마피아 채널 메시지...", key="mafia_chat_input")
            if st.button("마피아 전용 전송", key="mafia_chat_send"):
                if mafia_chat_input:
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/game/{game_id}/chat",
                            json={"sender": my_name, "content": mafia_chat_input, "channel": "mafia_secret"}
                        )
                        response.raise_for_status()
                        st.session_state.mafia_chat_input = ""
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "마피아 메시지 전송 실패")
    else:
        global_chats = [m for m in chat_history if m.get("channel") in ["global", "system"]]
        render_chat_list(global_chats)

        # Message Input for global chat
        is_chat_phase = phase in ["day_chat"]
        chat_input = st.text_input("메시지를 입력하세요...", key="chat_input", disabled=not is_chat_phase)
        if st.button("전송", key="chat_send", disabled=not is_chat_phase):
            if chat_input:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/game/{game_id}/chat",
                        json={"sender": my_name, "content": chat_input, "channel": "global"}
                    )
                    response.raise_for_status()
                    st.session_state.chat_input = ""
                except requests.exceptions.RequestException as e:
                    handle_request_error(e, "메시지 전송 실패")

if __name__ == "__main__":
    st.session_state.game_state = {
        "chat_history": [
            {"sender": "System", "content": "밤이 밝아왔습니다. 이지호 님이 사망했습니다."},
            {"sender": "김민준", "content": "어젯밤에 이지호가 죽었네...", "timestamp": "02:12"},
            {"sender": "박서연", "content": "저 왜 의심하세요?", "channel": "global", "timestamp": "02:15"},
            {"sender": "나", "content": "저는 이번에 최수아를 의심합니다.", "timestamp": "02:18"},
            {"sender": "마피아1", "content": "오늘 밤은 누구를?", "channel": "mafia_secret", "timestamp": "23:10"},
        ]
    }
    st.session_state.player_name = "나"
    draw_chat_area()
