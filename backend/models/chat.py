from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    id: str
    sender: str
    content: str
    channel: Literal["global", "mafia_secret", "spy_listen", "system"]
    timestamp: datetime
    is_ai: bool
