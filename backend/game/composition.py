"""GAME_RULES.md 인원표 기반 초기 직업 구성 (4~20인, 중간 인원은 시민 슬롯 가감)."""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from backend.models.game import Player, Role, Team

# (최대 인원, 역할별 개수) — 표에 없는 인원은 가장 가까운 하한 행 + 시민 추가
_COMPOSITION_ROWS: List[Tuple[int, Dict[str, int]]] = [
    (4, {"mafia": 1, "detective": 1, "citizen": 2}),
    (6, {"mafia": 1, "detective": 1, "doctor": 1, "citizen": 3}),
    (8, {"mafia": 2, "detective": 1, "doctor": 1, "citizen": 4}),
    (10, {"mafia": 2, "detective": 1, "doctor": 1, "jester": 1, "citizen": 5}),
    (
        12,
        {
            "mafia": 2,
            "detective": 1,
            "doctor": 1,
            "fortune_teller": 1,
            "jester": 1,
            "citizen": 6,
        },
    ),
    (
        15,
        {
            "mafia": 2,
            "killer": 1,
            "detective": 1,
            "doctor": 1,
            "fortune_teller": 1,
            "jester": 1,
            "spy": 1,
            "citizen": 7,
        },
    ),
    (
        20,
        {
            "mafia": 3,
            "killer": 1,
            "detective": 2,
            "doctor": 2,
            "fortune_teller": 1,
            "jester": 2,
            "spy": 1,
            "citizen": 8,
        },
    ),
]

_ROLE_KEYS: Dict[str, Role] = {
    "mafia": Role.MAFIA,
    "killer": Role.KILLER,
    "detective": Role.DETECTIVE,
    "doctor": Role.DOCTOR,
    "fortune_teller": Role.FORTUNE_TELLER,
    "jester": Role.JESTER,
    "spy": Role.SPY,
    "citizen": Role.CITIZEN,
}

_AI_NAME_POOL: List[str] = [
    "김민준",
    "박서연",
    "이지호",
    "최수아",
    "정하은",
    "강도윤",
    "윤서준",
    "한지우",
    "오채원",
    "신유진",
    "배준혁",
    "홍예린",
    "권민서",
    "조시우",
    "남다은",
    "류태양",
    "문하율",
    "안서연",
    "송지훈",
    "임채영",
]


def _team_for_role(role: Role) -> Team:
    if role in (Role.MAFIA, Role.KILLER):
        return Team.MAFIA
    if role in (Role.JESTER, Role.SPY):
        return Team.NEUTRAL
    return Team.CITIZEN


def role_multiset_for_player_count(player_count: int) -> List[Role]:
    if player_count < 4 or player_count > 20:
        raise ValueError("player_count는 4 이상 20 이하여야 합니다.")

    base_n, counts = max((n, c) for n, c in _COMPOSITION_ROWS if n <= player_count)
    extra = player_count - base_n
    if extra < 0:
        raise ValueError("invalid composition")

    merged = dict(counts)
    merged["citizen"] = merged.get("citizen", 0) + extra

    roles: List[Role] = []
    for key, n in merged.items():
        r = _ROLE_KEYS[key]
        roles.extend([r] * n)

    if len(roles) != player_count:
        raise RuntimeError("composition size mismatch")
    return roles


def build_initial_players(player_count: int, host_name: str) -> List[Player]:
    host = host_name.strip()
    if not host:
        raise ValueError("host_name이 비어 있습니다.")

    roles = role_multiset_for_player_count(player_count)
    random.shuffle(roles)

    taken_names = {host}
    ai_names: List[str] = []
    pool = [n for n in _AI_NAME_POOL if n != host]
    random.shuffle(pool)
    i = 0
    while len(ai_names) < player_count - 1:
        if i < len(pool):
            candidate = pool[i]
            i += 1
            if candidate in taken_names:
                continue
            taken_names.add(candidate)
            ai_names.append(candidate)
        else:
            suffix = len(ai_names) + 1
            candidate = f"AI_{suffix}"
            while candidate in taken_names:
                suffix += 1
                candidate = f"AI_{suffix}"
            taken_names.add(candidate)
            ai_names.append(candidate)

    names = [host] + ai_names
    players: List[Player] = []
    for name, role in zip(names, roles):
        players.append(
            Player(
                id=name,
                name=name,
                role=role,
                team=_team_for_role(role),
                is_alive=True,
                is_human=(name == host),
                trust_score=0.5,
            )
        )
    return players
