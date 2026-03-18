from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from backend.models.game import Role, Player, GameState


@dataclass
class RoleAbilityContext:
    game_state: GameState
    actor: Player
    target: Optional[Player]


AbilityHandler = Callable[[RoleAbilityContext], GameState]


def detective_investigate(ctx: RoleAbilityContext) -> GameState:
    return ctx.game_state


def doctor_protect(ctx: RoleAbilityContext) -> GameState:
    return ctx.game_state


def mafia_attack(ctx: RoleAbilityContext) -> GameState:
    return ctx.game_state


def killer_piercing_attack(ctx: RoleAbilityContext) -> GameState:
    return ctx.game_state


ROLE_ABILITIES: dict[Role, AbilityHandler] = {
    Role.DETECTIVE: detective_investigate,
    Role.DOCTOR: doctor_protect,
    Role.MAFIA: mafia_attack,
    Role.KILLER: killer_piercing_attack,
}
