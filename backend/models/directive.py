from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Directive(BaseModel):
    target_agent: str
    from_: str = Field(validation_alias="from", serialization_alias="from")
    type: str
    content: str
    priority: Literal["low", "medium", "high"] = "medium"
    round: int


class Report(BaseModel):
    agent_id: str
    content: str
    round: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
