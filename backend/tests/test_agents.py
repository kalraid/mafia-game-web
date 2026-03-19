from __future__ import annotations

import asyncio

from backend.agents.persona import DEFAULT_PERSONAS
from backend.agents.graph import AgentGraph
from backend.agents.pool import AgentPool
from backend.agents.player_agent import AgentInput, PlayerAgent
from backend.game.engine import GameEngine
from backend.models.game import GameState, Phase, Player, Role, Team


def test_player_agent_runs_with_or_without_llm() -> None:
    # 테스트 환경에서 ANTHROPIC_API_KEY가 없을 수 있으므로 "실패 없이" 실행 가능해야 함
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
            ),
        ],
        chat_history=[],
    )
    agent = PlayerAgent(
        agent_id="p1",
        persona=DEFAULT_PERSONAS[0],
        player=state.players[0],
    )

    out = asyncio.run(
        agent.run(
            AgentInput(game_state=state, my_state=state.players[0], supervisor_directive=None)
        )
    )
    assert out is not None


def test_player_agent_night_mafia_fallback_speech() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.NIGHT_MAFIA,
        round=1,
        timer_seconds=90,
        players=[
            Player(
                id="m1",
                name="마피아1",
                role=Role.MAFIA,
                team=Team.MAFIA,
                is_alive=True,
                is_human=False,
            ),
            Player(
                id="c1",
                name="시민1",
                role=Role.CITIZEN,
                team=Team.CITIZEN,
                is_alive=True,
                is_human=False,
            ),
        ],
        chat_history=[],
    )

    agent = PlayerAgent(
        agent_id="m1",
        persona=DEFAULT_PERSONAS[0],
        player=state.players[0],
    )

    out = asyncio.run(
        agent.run(
            AgentInput(
                game_state=state,
                my_state=state.players[0],
                supervisor_directive=None,
            )
        )
    )

    assert out.speech is not None
    assert out.vote is None
    assert out.action is None


def test_agent_graph_night_mafia_sends_mafia_secret_chat() -> None:
    state = GameState(
        game_id="g1",
        phase=Phase.NIGHT_MAFIA,
        round=1,
        timer_seconds=90,
        players=[
            Player(
                id="m1",
                name="마피아1",
                role=Role.MAFIA,
                team=Team.MAFIA,
                is_alive=True,
                is_human=False,
            ),
            Player(
                id="c1",
                name="시민1",
                role=Role.CITIZEN,
                team=Team.CITIZEN,
                is_alive=True,
                is_human=False,
            ),
        ],
        chat_history=[],
    )
    engine = GameEngine(state)

    pool = AgentPool()
    pool.create_agents(players=[p for p in state.players if p.is_alive and not p.is_human])
    agents = {a.agent_id: a for a in pool.all_agents()}

    graph = AgentGraph(engine=engine, agents=agents)

    asyncio.run(graph.run_night_mafia_round(engine.state))

    assert any(msg.channel == "mafia_secret" for msg in engine.state.chat_history)
    assert all(msg.channel == "mafia_secret" for msg in engine.state.chat_history)

