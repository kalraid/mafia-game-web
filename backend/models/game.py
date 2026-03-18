from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict

from pydantic import BaseModel, Field

from backend.models.chat import ChatMessage
from backend.models.directive import Directive, Report

class Team(str, Enum):
    CITIZEN = "citizen"
    MAFIA = "mafia"
    NEUTRAL = "neutral"


class Role(str, Enum):
    CITIZEN = "citizen"
    DETECTIVE = "detective"
    DOCTOR = "doctor"
    FORTUNE_TELLER = "fortune_teller"
    MAFIA = "mafia"
    KILLER = "killer"
    JESTER = "jester"
    SPY = "spy"


class Phase(str, Enum):
    DAY_CHAT = "day_chat"
    DAY_VOTE = "day_vote"
    FINAL_SPEECH = "final_speech"
    FINAL_VOTE = "final_vote"
    NIGHT_MAFIA = "night_mafia"
    NIGHT_ABILITY = "night_ability"
    NIGHT_RESULT = "night_result"


class Player(BaseModel):
    id: str
    name: str
    role: Role
    team: Team
    is_alive: bool = True
    is_human: bool = False
    trust_score: float = 0.5
    ability_used: bool = False


class GameEvent(BaseModel):
    type: str
    payload: Dict[str, object] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GameState(BaseModel):
    game_id: str
    phase: Phase
    round: int
    timer_seconds: int
    players: List[Player]
    chat_history: List[ChatMessage] = Field(default_factory=list)
    events: List[GameEvent] = Field(default_factory=list)
    winner: Optional[str] = None  # "citizen" | "mafia" | "jester" | "spy"

    directives: List[Directive] = Field(default_factory=list)
    reports: List[Report] = Field(default_factory=list)
