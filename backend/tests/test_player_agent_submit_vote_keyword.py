from __future__ import annotations

import asyncio

import pytest

from backend.agents.persona import DEFAULT_PERSONAS
from backend.agents.player_agent import AgentInput, PlayerAgent
from backend.game.engine import GameEngine
from backend.mcp.tools import MCPGameTools
from backend.models.game import GameState, Phase, Player, Role, Team


def test_player_agent_tool_exec_submit_vote_uses_agent_id(monkeypatch: pytest.MonkeyPatch) -> None:
    # LLM 비동기/실제 API 호출을 막기 위해 ChatAnthropic을 Fake로 대체한다.
    class FakeToolMsg:
        tool_calls = [{"name": "submit_vote", "args": {"target_id": "p2"}}]

    class FakeChatAnthropic:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def bind_tools(self, tools):  # noqa: ANN001
            return self

        def invoke(self, messages):  # noqa: ANN001
            return FakeToolMsg()

        def with_structured_output(self, schema):  # noqa: ANN001
            raise AssertionError("structured_output 경로는 호출되면 안 됩니다(툴 실행 성공 기준)")

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("MAFIA_USE_LLM", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")

    # RAG는 이 테스트에서 필요 없으니 초기화 비용/의존성을 제거
    state = GameState(
        game_id="g1",
        phase=Phase.DAY_VOTE,
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

    # ChatAnthropic만 Fake로 대체
    import langchain_anthropic  # type: ignore

    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", FakeChatAnthropic)

    agent_input = AgentInput(game_state=state, my_state=state.players[0], supervisor_directive=None)
    decision, executed_any, _rag = asyncio.run(agent._decide_with_llm(agent_input))

    assert executed_any is True
    assert decision.vote_target == "p2"
    assert engine.get_vote_snapshot()["p1"] == "p2"

