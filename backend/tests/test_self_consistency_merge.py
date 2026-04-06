from __future__ import annotations

from backend.agents.player_agent import AgentDecision, merge_agent_decisions_self_consistency
from backend.models.game import Phase


def test_merge_vote_majority() -> None:
    d = merge_agent_decisions_self_consistency(
        [
            AgentDecision(vote_target="p1", reasoning="a", confidence=0.5),
            AgentDecision(vote_target="p2", reasoning="b", confidence=0.6),
            AgentDecision(vote_target="p2", reasoning="c", confidence=0.7),
        ],
        Phase.DAY_VOTE,
    )
    assert d.vote_target == "p2"
    assert d.speech is None


def test_merge_ability_pair_majority() -> None:
    d = merge_agent_decisions_self_consistency(
        [
            AgentDecision(ability="investigate", ability_target="p4", reasoning="x", confidence=0.4),
            AgentDecision(ability="investigate", ability_target="p4", reasoning="y", confidence=0.5),
            AgentDecision(ability="heal", ability_target="p1", reasoning="z", confidence=0.6),
        ],
        Phase.NIGHT_ABILITY,
    )
    assert d.ability == "investigate"
    assert d.ability_target == "p4"


def test_merge_longest_speech() -> None:
    d = merge_agent_decisions_self_consistency(
        [
            AgentDecision(speech="짧음", reasoning="a", confidence=0.3),
            AgentDecision(speech="이게 가장 긴 발언 텍스트입니다.", reasoning="b", confidence=0.4),
        ],
        Phase.DAY_CHAT,
    )
    assert "긴 발언" in (d.speech or "")
