import streamlit as st
from components.chat_area import draw_chat_area
from components.status_panel import draw_status_panel

def draw_game():
    col1, col2 = st.columns([3, 1])

    with col1:
        draw_chat_area()

    with col2:
        draw_status_panel()

if __name__ == "__main__":
    draw_game()
