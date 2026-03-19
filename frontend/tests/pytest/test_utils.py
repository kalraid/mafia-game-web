import pytest
import requests
from unittest.mock import Mock, patch
from frontend.utils import handle_request_error

@patch('frontend.utils.st')
def test_handle_request_error_connection_error(mock_st):
    """
    Tests if a ConnectionError produces the correct user-friendly message.
    """
    # Arrange
    error = requests.exceptions.ConnectionError("Failed to establish a new connection.")
    default_message = "테스트 실패"
    expected_message = f"{default_message}: 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요."

    # Act
    handle_request_error(error, default_message)

    # Assert
    mock_st.error.assert_called_once_with(expected_message)

@patch('frontend.utils.st')
def test_handle_request_error_http_500_error(mock_st):
    """
    Tests if a 500 HTTPError produces the correct server error message.
    """
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 500
    error = requests.exceptions.HTTPError(response=mock_response)
    default_message = "테스트 실패"
    expected_message = f"{default_message}: 서버에 문제가 발생했습니다 (코드: 500). 잠시 후 다시 시도해주세요."

    # Act
    handle_request_error(error, default_message)

    # Assert
    mock_st.error.assert_called_once_with(expected_message)

@patch('frontend.utils.st')
def test_handle_request_error_http_400_error_with_json(mock_st):
    """
    Tests if a 400 HTTPError with a JSON body produces the correct detailed message.
    """
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"detail": "Invalid input provided."}
    error = requests.exceptions.HTTPError(response=mock_response)
    default_message = "테스트 실패"
    expected_message = f"{default_message}: 잘못된 요청입니다 (코드: 400). 내용: Invalid input provided."

    # Act
    handle_request_error(error, default_message)

    # Assert
    mock_st.error.assert_called_once_with(expected_message)

@patch('frontend.utils.st')
def test_handle_request_error_timeout(mock_st):
    """
    Tests if a Timeout exception produces the correct user-friendly message.
    """
    # Arrange
    error = requests.exceptions.Timeout("Request timed out.")
    default_message = "테스트 실패"
    expected_message = f"{default_message}: 요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요."

    # Act
    handle_request_error(error, default_message)

    # Assert
    mock_st.error.assert_called_once_with(expected_message)
