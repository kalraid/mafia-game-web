import streamlit as st

def draw_player_card(player_name, is_alive=True, is_me=False, votes=0, disabled=False, role=None, is_silent=False):
    """
    Draws a player card using st.markdown for full CSS styling.
    The card is made clickable by wrapping it in an <a> tag that sets a query parameter.
    If the player is dead and a role is provided, it's shown in the overlay.
    Shows a silent icon if the player has been silent.
    """
    
    # Build class string for CSS
    class_list = ["player-card"]
    if is_me:
        class_list.append("is-me")
    if not is_alive:
        class_list.append("is-dead")
    if disabled and is_alive: # Don't apply to dead players, already styled
        class_list.append("is-disabled")
    
    if votes > 0 and is_alive:
        suspicion_level = min(votes, 3)
        class_list.append(f"is-suspected-{suspicion_level}")
    
    class_str = " ".join(class_list)

    icon = "💀" if not is_alive else "👤"
    
    label_name = f"⭐ {player_name} (나)" if is_me else player_name
    
    silent_icon = "🤫" if is_silent and is_alive else ""
    
    label = f"{icon} {label_name} {silent_icon}"
    if votes > 0 and is_alive:
        label += f" [{votes}표]"
        
    # The link is disabled via CSS if needed
    href = f"?select={player_name}" if not disabled and is_alive else "#"

    # Generate the death overlay HTML if the player is not alive
    dead_overlay_html = ""
    if not is_alive:
        dead_text = "사망"
        if role:
            dead_text += f"<br><small>({role})</small>"
        dead_overlay_html = f'<div class="death-overlay">{dead_text}</div>'

    st.markdown(f'''
        <a href="{href}" target="_self" class="player-card-link">
            <div class="{class_str}">
                {label}
                {dead_overlay_html}
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
