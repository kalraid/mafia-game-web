from playwright.sync_api import Page, expect
import pytest

# Mark this test as E2E
@pytest.mark.e2e
def test_lobby_to_game_navigation(page: Page):
    """
    Tests that a user can enter a nickname, start the game,
    and successfully navigate from the lobby page to the game page.
    
    This test assumes the Streamlit app is running on localhost:8501.
    """
    # Act: Navigate to the Streamlit app's URL
    # The base_url can be configured in pytest.ini or passed via command line
    # For now, we assume it's running locally.
    try:
        page.goto("http://localhost:8501")
    except Exception as e:
        pytest.fail(f"Could not connect to Streamlit app at http://localhost:8501. Is the app running? Error: {e}")

    # Arrange: Get page elements, using corrected selectors from G-14
    nickname_input = page.get_by_label("닉네임")
    start_button = page.get_by_role("button", name="게임 시작 🎮")

    # Assert: Verify that the initial elements are visible
    expect(nickname_input).to_be_visible(timeout=10000) # Increased timeout for initial load
    expect(start_button).to_be_visible()

    # Act: Fill the nickname and click the start button
    nickname_input.fill("E2E_Test_Player")
    start_button.click()

    # Assert: Check that the game page is now visible
    # We look for an element that is unique to the game page, like the "Status" header.
    # st.header() creates an <h2> element.
    game_screen_status_header = page.get_by_role("heading", name="Status", level=2)
    
    # The page reruns and components load, so we give it a moment
    expect(game_screen_status_header).to_be_visible(timeout=5000)

    # Also check that the lobby's title is no longer visible
    # st.title() creates an <h1> element, but the work order for G-14 was specific about changing it to level=2.
    # Let's trust the work order for now. If it fails, we know st.title creates an h1.
    # After checking the lobby.py, st.title("🎭 AI Mafia Online") is used. Let's assume the work order is correct about the level.
    lobby_title = page.get_by_role("heading", name="🎭 AI Mafia Online", level=1)
    expect(lobby_title).not_to_be_visible()
