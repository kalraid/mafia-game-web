from playwright.sync_api import Page, expect
import pytest

@pytest.mark.e2e
def test_game_page_elements(page: Page):
    """
    Tests the main components of the game page (chat area, status panel)
    after starting a game from the lobby.
    """
    try:
        page.goto("http://localhost:8501")
    except Exception as e:
        pytest.fail(f"Could not connect to Streamlit app. Error: {e}")

    # Login and start game
    nickname_input = page.get_by_label("닉네임")
    start_button = page.get_by_role("button", name="게임 시작 🎮")
    
    expect(nickname_input).to_be_visible(timeout=10000)
    nickname_input.fill("E2E_Game_Tester")
    start_button.click()

    # Check Status Panel elements
    status_header = page.get_by_role("heading", name="Status", level=2)
    expect(status_header).to_be_visible(timeout=10000)

    # In day_chat phase, we should see Chat header
    chat_header = page.get_by_role("heading", name="Chat", level=2)
    expect(chat_header).to_be_visible()

    # Check for Chat input and send button
    # In chat_area.py: st.text_input("메시지를 입력하세요...", key="chat_input")
    chat_input = page.get_by_label("메시지를 입력하세요...")
    send_button = page.get_by_role("button", name="전송")
    
    expect(chat_input).to_be_visible()
    expect(send_button).to_be_visible()

    # Send a message
    chat_input.fill("E2E Test Message")
    send_button.click()

    # Verify RAG context panel exists (G-12)
    rag_expander = page.get_by_text("🔍 RAG 컨텍스트 (디버그)")
    expect(rag_expander).to_be_visible()
