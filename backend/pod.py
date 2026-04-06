"""POD(프로세스) 식별 — 멀티 레플리카 환경에서 소유권 로깅용."""

from __future__ import annotations

import os
import socket


def get_pod_id() -> str:
    """
    현재 프로세스(POD)의 식별자를 반환한다.
    우선순위: 환경변수 MAFIA_POD_ID > 컨테이너 hostname > 로컬 hostname
    """
    explicit = os.getenv("MAFIA_POD_ID", "").strip()
    if explicit:
        return explicit
    return socket.gethostname()


# 모듈 로드 시 1회만 계산
POD_ID: str = get_pod_id()
