from __future__ import annotations

import asyncio

from backend.agents.persona import DEFAULT_PERSONAS
from backend.agents.player_agent import AgentInput, PlayerAgent
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

