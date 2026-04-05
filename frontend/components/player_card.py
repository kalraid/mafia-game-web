import streamlit as st

def draw_player_card(player_name, is_alive=True, is_me=False, votes=0, disabled=False, role=None, is_silent=False, trust_score=0.5):
    """
    Draws a player card using st.markdown for full CSS styling.
    """
    
    # Build class string for CSS
    class_list = ["player-card"]
    if is_me:
        class_list.append("is-me")
    
    if not is_alive:
        class_list.append("dead-overlay")
        
    if disabled and is_alive:
        class_list.append("is-disabled")
    
    # Apply suspicion level based on trust_score (G-9)
    # Lower trust_score means higher suspicion level (1 to 3)
    if is_alive and not is_me:
        if trust_score < 0.2:
            class_list.append("is-suspected-3")
        elif trust_score < 0.4:
            class_list.append("is-suspected-2")
        elif trust_score < 0.6:
            class_list.append("is-suspected-1")
    
    class_str = " ".join(class_list)

    icon = "💀" if not is_alive else "👤"
    
    label_name = f"⭐ {player_name} (나)" if is_me else player_name
    
    # If dead and role is revealed, show it (G-6)
    role_info = f" ({role})" if not is_alive and role else ""
    
    silent_icon = "🤫" if is_silent and is_alive else ""
    
    label = f"{icon} {label_name}{role_info} {silent_icon}"
    if votes > 0 and is_alive:
        label += f" [{votes}표]"
        
    href = f"?select={player_name}" if not disabled and is_alive else "#"

    st.markdown(f'''
        <a href="{href}" target="_self" class="player-card-link">
            <div class="{class_str}">
                {label}
            </div>
        </a>
    ''', unsafe_allow_html=True)

if __name__ == '__main__':
    st.subheader("Player Card Examples (Styled & Clickable)")

    # Add custom CSS for the link wrapper
    st.markdown("""
        <style>
            /* This is a slimmed down version of style.css for example purposes */
            .player-card { border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 5px; position: relative; }
            .player-card.is-dead { background-color: #424242; color: #9E9E9E; text-decoration: line-through; }
            .death-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.75); color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; font-weight: bold; text-align: center; }
            .player-card-link { text-decoration: none; color: inherit; }
            .is-disabled { opacity: 0.5; cursor: not-allowed; }
        </style>
    """, unsafe_allow_html=True)
    
    st.write("These cards now show role on death and silent status.")
    draw_player_card("김민준", is_alive=True, votes=1, is_silent=True)
    draw_player_card("나", is_alive=True, is_me=True, votes=0)
    draw_player_card("최수아", is_alive=False, role="경찰")
    draw_player_card("이지호", is_alive=False)
    draw_player_card("박서연", is_alive=True, votes=0, disabled=True)
