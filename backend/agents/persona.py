from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class AgentPersona(BaseModel):
    name: str
    speech_style: Literal["격식체", "반말", "조심스러운", "공격적"]
    aggression: float  # 0.0 ~ 1.0
    trust_tendency: float  # 0.0 ~ 1.0
    verbosity: float  # 0.0 ~ 1.0
    logic_style: Literal["감정형", "논리형", "직관형"]


DEFAULT_PERSONAS: list[AgentPersona] = [
    AgentPersona(
        name="김민준",
        speech_style="반말",
        aggression=0.8,
        trust_tendency=0.4,
        verbosity=0.7,
        logic_style="직관형",
    ),
    AgentPersona(
        name="박서연",
        speech_style="격식체",
        aggression=0.3,
        trust_tendency=0.6,
        verbosity=0.4,
        logic_style="논리형",
    ),
]
