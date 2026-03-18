import streamlit as st

def draw_player_card(player_name, is_alive=True, is_me=False, votes=0):
    
    # Build class string
    class_list = ["player-card"]
    if is_me:
        class_list.append("is-me")
    if not is_alive:
        class_list.append("is-dead")
    
    if votes > 0:
        suspicion_level = min(votes, 3) # Cap at 3 for styling
        class_list.append(f"is-suspected-{suspicion_level}")
    
    class_str = " ".join(class_list)

    icon = "💀" if not is_alive else "👤"
    
    st.markdown(f'<div class="{class_str}">{icon} {player_name}</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    st.subheader("Player Card Examples")
    draw_player_card("김민준", is_alive=True, votes=0)
    draw_player_card("나", is_alive=True, is_me=True, votes=1)
    draw_player_card("의심 많이", is_alive=True, votes=3)
    draw_player_card("이지호", is_alive=False)
