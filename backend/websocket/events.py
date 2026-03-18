from __future__ import annotations

from typing import Literal, Any

from pydantic import BaseModel


class ClientToServerEvent(BaseModel):
    event: Literal["chat_message", "vote", "use_ability"]
    payload: dict[str, Any]


class ChatMessagePayload(BaseModel):
    content: str
    sender: str


class VotePayload(BaseModel):
    target: str


class UseAbilityPayload(BaseModel):
    target: str
    ability: str


class ServerToClientEvent(BaseModel):
    event: Literal[
        "chat_broadcast",
        "phase_change",
        "player_death",
        "game_state_update",
        "vote_result",
        "ability_result",
        "game_over",
    ]
    payload: dict[str, Any]
