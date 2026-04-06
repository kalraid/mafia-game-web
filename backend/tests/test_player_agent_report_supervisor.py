"""GAP-01: LLM tool 경로에서 report_to_supervisor가 state.reports에 반영되는지 검증."""

from __future__ import annotations

import asyncio

import pytest

from backend.agents.persona import DEFAULT_PERSONAS
from backend.agents.player_agent import AgentInput, PlayerAgent
from backend.game.engine import GameEngine
from backend.mcp.tools import MCPGameTools
from backend.models.game import GameState, Phase, Player, Role, Team


def test_player_agent_tool_exec_report_to_supervisor(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeToolMsg:
        tool_calls = [{"name": "report_to_supervisor", "args": {"report": "p2가 마피아로 보임"}}]

    class FakeChatAnthropic:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def bind_tools(self, tools):  # noqa: ANN001
            return self

        def invoke(self, messages):  # noqa: ANN001
            return FakeToolMsg()

        def with_structured_output(self, schema):  # noqa: ANN001
            raise AssertionError("structured_output 경로는 호출되면 안 됩니다")

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")

    state = GameState(
        game_id="g1",
        phase=Phase.DAY_CHAT,
        round=1,
        timer_seconds=60,
        players=[
            Player(id="p1", name="A", role=Role.CITIZEN, team=Team.CITIZEN, is_alive=True),
            Player(id="p2", name="B", role=Role.MAFIA, team=Team.MAFIA, is_alive=True),
        ],
        chat_history=[],
        events=[],
    )
    engine = GameEngine(state)

    agent = PlayerAgent(
        agent_id="p1",
        persona=DEFAULT_PERSONAS[0],
        player=state.players[0],
        mcp_tools=MCPGameTools(engine=engine),
    )
    monkeypatch.setattr(agent, "_get_rag_retriever", lambda: None)

    import langchain_anthropic  # type: ignore

    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", FakeChatAnthropic)

    agent_input = AgentInput(game_state=state, my_state=state.players[0], supervisor_directive=None)
    decision, executed_any, _rag = asyncio.run(agent._decide_with_llm(agent_input))

    assert executed_any is True
    assert len(state.reports) == 1
    assert state.reports[0].agent_id == "p1"
    assert "p2" in state.reports[0].content or "마피아" in state.reports[0].content
    assert "report_to_supervisor" in (decision.reasoning or "")
