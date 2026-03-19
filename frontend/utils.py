import streamlit as st
import requests

def handle_request_error(e: requests.exceptions.RequestException, default_message: str):
    """
    Provides user-friendly error messages for requests exceptions.
    """
    try:
        # If the exception is an HTTPError, we might have a response object
        if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
            status_code = e.response.status_code
            if status_code >= 500:
                st.error(f"{default_message}: 서버에 문제가 발생했습니다 (코드: {status_code}). 잠시 후 다시 시도해주세요.")
            elif status_code >= 400:
                # Try to get a detailed message from the backend response
                try:
                    details = e.response.json().get("detail", "서버가 구체적인 오류를 반환하지 않았습니다.")
                except requests.exceptions.JSONDecodeError:
                    details = e.response.text
                st.error(f"{default_message}: 잘못된 요청입니다 (코드: {status_code}). 내용: {details}")
            else:
                st.error(f"{default_message}: {e}")
        elif isinstance(e, requests.exceptions.ConnectionError):
            st.error(f"{default_message}: 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.")
        elif isinstance(e, requests.exceptions.Timeout):
            st.error(f"{default_message}: 요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요.")
        else:
            # For other request-related errors
            st.error(f"{default_message}: 알 수 없는 네트워크 오류가 발생했습니다. {e}")
    except Exception as final_e:
        # Fallback for any other issue during error handling itself
        st.error(f"{default_message}: 알 수 없는 오류가 발생했습니다. {final_e}")
