import streamlit as st
import requests
from datetime import datetime

def draw_chat_area():
    st.header("Chat")

    game_state = st.session_state.get("game_state", {})
    chat_history = game_state.get("chat_history", [])
    my_name = st.session_state.get("player_name", "Player")
    game_id = st.session_state.get("game_id", "test_game")

    # Chat History
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in chat_history:
        sender = msg.get("sender", "System")
        content = msg.get("content", "")
        channel = msg.get("channel", "global")
        timestamp = msg.get("timestamp", datetime.now().strftime("%H:%M"))

        class_list = ["chat-message"]
        sender_display = sender

        if sender == "System":
            class_list.append("system-message")
            st.markdown(f'<div class="{" ".join(class_list)}">{content}</div>', unsafe_allow_html=True)
            continue # Skip to next message
        elif sender == my_name:
            class_list.append("my-message")
            sender_display = f"🟢 {my_name}"
        elif channel == "mafia_secret":
            class_list.append("mafia-message")
            sender_display = f"🔴 {sender} (마피아)"
        else:
            class_list.append("other-message")
            sender_display = f"👤 {sender}"

        st.markdown(f"""
            <div class="{" ".join(class_list)}">
                <div class="message-header">
                    <span>{sender_display}</span>
                    <span>{timestamp}</span>
                </div>
                <div class="message-content">
                    {content}
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # JavaScript for auto-scrolling
    st.markdown("""
        <script>
            const chatContainer = window.parent.document.querySelector('.chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        </script>
    """, unsafe_allow_html=True)


    # Message Input
    chat_input = st.text_input("메시지를 입력하세요...", key="chat_input")
    if st.button("전송", key="chat_send"):
        if chat_input:
            try:
                # Send message to backend via HTTP POST
                response = requests.post(
                    f"http://localhost:8000/game/{game_id}/chat",
                    json={"sender": my_name, "content": chat_input, "channel": "global"}
                )
                response.raise_for_status()
                st.session_state.chat_input = ""
            except requests.exceptions.RequestException as e:
                st.error(f"메시지 전송 실패: {e}")

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
