from __future__ import annotations

from typing import List

from backend.game.engine import GameEngine
from backend.models.chat import ChatMessage
from backend.models.directive import Directive, Report
from backend.models.game import GameState, Player, Role, Phase


class MCPGameTools:
    """
    AGENT_DESIGN 문서의 MCP Tool 인터페이스 스켈레톤.
    실제 MCP 서버 바인딩은 server.py에서 처리.
    """

    def __init__(self, engine: GameEngine) -> None:
        self.engine = engine

    # Game State Tools
    def get_alive_players(self) -> List[Player]:
        state: GameState = self.engine.state
        return [p for p in state.players if p.is_alive]

    def get_chat_history(self, last_n: int = 20) -> List[ChatMessage]:
        state: GameState = self.engine.state
        return state.chat_history[-last_n:]

    def get_my_role(self, agent_id: str) -> Role:
        state: GameState = self.engine.state
        player = next(p for p in state.players if p.id == agent_id)
        return player.role

    def get_current_phase(self) -> Phase:
        return self.engine.state.phase

    def get_supervisor_directives(self, agent_id: str) -> List[Directive]:
        state: GameState = self.engine.state
        return [d for d in state.directives if d.target_agent == agent_id]

    # Action Tools
    def send_chat(self, agent_id: str, content: str, channel: str = "global") -> bool:
        # Phase 5에서는 GameState에만 기록하고, WebSocket 브로드캐스트 연동은 이후 단계에서 처리
        return True

    def submit_vote(self, agent_id: str, target_id: str) -> bool:
        # GameEngine.votes에 기록하는 로직은 이후 Phase에서 추가
        return True

    def use_ability(self, agent_id: str, ability: str, target_id: str) -> bool:
        # roles.py의 ROLE_ABILITIES와 연동하는 실제 처리 로직은 이후 Phase에서 추가
        return True

    def report_to_supervisor(self, agent_id: str, report: str) -> bool:
        state: GameState = self.engine.state
        state.reports.append(
            Report(
                agent_id=agent_id,
                content=report,
                round=state.round,
            )
        )
        return True

    # Supervisor-only Tools
    def issue_directive(self, supervisor_id: str, target_agent: str, directive: Directive) -> bool:
        state: GameState = self.engine.state
        state.directives.append(directive)
        return True

    def get_all_reports(self, supervisor_id: str) -> List[Report]:
        return self.engine.state.reports

    def analyze_trust_scores(self) -> dict[str, float]:
        state: GameState = self.engine.state
        return {p.id: p.trust_score for p in state.players}
