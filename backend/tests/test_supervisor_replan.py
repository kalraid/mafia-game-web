from __future__ import annotations

from backend.agents.graph import AgentGraph
from backend.game.engine import GameEngine
from backend.models.directive import Report
from backend.models.game import GameState, Phase, Player, Role, Team


def test_supervisor_replan_reduces_trust_when_report_mentions_mafia() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(
                id="p1",
                name="A",
                role=Role.CITIZEN,
                team=Team.CITIZEN,
                is_alive=True,
                is_human=False,
                trust_score=0.5,
            ),
            Player(
                id="p2",
                name="B",
                role=Role.CITIZEN,
                team=Team.CITIZEN,
                is_alive=True,
                is_human=False,
                trust_score=0.5,
            ),
        ],
        chat_history=[],
        events=[],
        directives=[],
        reports=[
            Report(agent_id="agentX", content="B는 mafia입니다.", round=1),
        ],
    )
    engine = GameEngine(state)
    graph = AgentGraph(engine=engine, agents={})

    graph.supervisor_replan(state)

    p2 = next(p for p in state.players if p.id == "p2")
    assert p2.trust_score <= 0.2
    assert state.reports == []

