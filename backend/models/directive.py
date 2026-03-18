from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Directive(BaseModel):
    target_agent: str
    from_: str
    type: str
    content: str
    priority: Literal["low", "medium", "high"] = "medium"
    round: int


class Report(BaseModel):
    agent_id: str
    content: str
    round: int
    created_at: datetime
