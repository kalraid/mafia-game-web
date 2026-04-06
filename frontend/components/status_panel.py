import streamlit as st
import requests
import os
from components.player_card import draw_player_card
from frontend.utils import handle_request_error

# Use environment variable for containerized setup, with a fallback for local dev
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

def draw_status_panel():
    # Handle selection from query parameters, which is set by clicking a player card
    if "select" in st.query_params:
        selected_player = st.query_params["select"]
        # Toggle selection
        if st.session_state.get("selection") == selected_player:
            st.session_state.selection = None
        else:
            st.session_state.selection = selected_player
        
        # Clear query params to prevent re-triggering on the next rerun
        st.query_params.clear()
        st.rerun()

    st.header("Status")

    
    game_state = st.session_state.get("game_state", {})

    # Phase Display
    phase = game_state.get("phase", "day_chat")
    round_num = game_state.get("round", 0)
    timer_seconds = game_state.get("timer_seconds", 0)

    phase_map = {
        "day_chat": {"icon": "☀️", "text": "낮 토론", "max_time": 180},
        "day_vote": {"icon": "🗳️", "text": "낮 투표", "max_time": 60},
        "final_speech": {"icon": "💬", "text": "최후 변론", "max_time": 30},
        "night": {"icon": "🌙", "text": "밤", "max_time": 90},
        "result": {"icon": "🔔", "text": "결과", "max_time": 10},
        "대기": {"icon": "⏳", "text": "대기", "max_time": 10}
    }
    
    current_phase_info = phase_map.get(phase, {"icon": "❓", "text": phase, "max_time": timer_seconds})
    phase_class = f"phase-{phase}"
    
    timer_js = f"""
    <script>
    // Clear any existing timer to avoid multiple intervals running
    if (window.mafiaTimerInterval) {{
        clearInterval(window.mafiaTimerInterval);
    }}

    function startTimer(duration, display) {{
        let timer = duration;
        window.mafiaTimerInterval = setInterval(function () {{
            let minutes = parseInt(timer / 60, 10);
            let seconds = parseInt(timer % 60, 10);

            minutes = minutes < 10 ? "0" + minutes : minutes;
            seconds = seconds < 10 ? "0" + seconds : seconds;

            display.textContent = minutes + ":" + seconds;

            if (--timer < 0) {{
                clearInterval(window.mafiaTimerInterval);
                // Optionally trigger a rerun when timer ends, though server should do this
            }}
        }}, 1000);
    }}

    // We need to use parent.document because Streamlit runs in an iframe
    const timerDisplay = window.parent.document.querySelector('#mafia-timer-display');
    if (timerDisplay) {{
        startTimer({timer_seconds}, timerDisplay);
    }}
    </script>
    """

    with st.container():
        st.markdown(f"""
            <div class="phase-display {phase_class}">
                <h3>{current_phase_info['icon']} {current_phase_info['text']} {round_num}라운드</h3>
            </div>
            <div class="stMetric">
                <label style="display: block; text-align: center; font-size: 1rem;">남은 시간</label>
                <div data-testid="stMetricValue" style="font-size: 2.25rem; text-align: center;" id="mafia-timer-display">{timer_seconds // 60:02d}:{timer_seconds % 60:02d}</div>
            </div>
            {timer_js}
        """, unsafe_allow_html=True)
        
        max_time = current_phase_info.get("max_time", timer_seconds)
        st.progress(timer_seconds / max_time if max_time > 0 else 0)

    # Player List
    with st.container():
        players = game_state.get("players", [])
        st.subheader(f"플레이어 ({len([p for p in players if p.get('is_alive', False)])}/{len(players)})")
        
        my_name = st.session_state.get("player_name", "")
        phase = game_state.get("phase", "day_chat")
        
        interaction_allowed = phase in ["day_chat", "day_vote", "night"]
        
        if "selection" not in st.session_state:
            st.session_state.selection = None

        if st.session_state.selection:
            st.success(f"현재 선택: **{st.session_state.selection}**")

        for player in players:
            is_me = player.get("name") == my_name
            player_name = player.get("name", "Unknown")
            is_alive = player.get("is_alive", True)
            is_selectable = is_alive and not is_me
            
            draw_player_card(
                player_name=player_name,
                is_alive=is_alive,
                is_me=is_me,
                votes=player.get("votes", 0),
                disabled=not (interaction_allowed and is_selectable),
                role=player.get("role"),
                is_silent=player.get("is_silent", False),
                trust_score=player.get("trust_score", 0.5)
            )

    # Button Area
    with st.container():
        st.subheader("행동")
        phase = game_state.get("phase", "day_chat")
        my_role = st.session_state.get("my_role", "citizen")

        if phase == "day_chat":
            st.write("조사할 플레이어의 채팅을 보려면 카드를 클릭하세요.")
            if st.button("게임 설정"):
                pass
        elif phase == "day_vote":
            st.write("투표할 플레이어를 클릭하세요.")
            if st.button("투표 완료", type="primary"):
                if st.session_state.selection:
                    try:
                        my_name = st.session_state.get("player_name", "UnknownPlayer")
                        game_id = st.session_state.get("game_id", "test_game")
                        target_name = st.session_state.selection
                        
                        response = requests.post(
                            f"{BACKEND_URL}/game/{game_id}/vote",
                            json={"voter": my_name, "voted_for": target_name}
                        )
                        response.raise_for_status()
                        
                        st.toast(f"✅ {target_name}에게 투표했습니다.", icon="✅")
                        st.session_state.selection = None
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "투표 전송 실패")
                else:
                    st.warning("투표할 대상을 먼저 선택해주세요.")

            if st.button("기권(무투표)"):
                try:
                    my_name = st.session_state.get("player_name", "UnknownPlayer")
                    game_id = st.session_state.get("game_id", "test_game")
                    
                    response = requests.post(
                        f"{BACKEND_URL}/game/{game_id}/vote",
                        json={"voter": my_name, "voted_for": None}
                    )
                    response.raise_for_status()

                    st.toast("✅ 기권했습니다.", icon="🏳️")
                    st.session_state.selection = None
                    st.rerun()
                except requests.exceptions.RequestException as e:
                    handle_request_error(e, "기권 처리 실패")

        elif phase == "final_speech":
            execution_target = game_state.get("execution_target")
            if execution_target:
                st.write(f"**{execution_target}**의 최후 변론입니다. 처형 여부를 투표하세요.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 처형 찬성", disabled=not execution_target):
                    try:
                        my_name = st.session_state.get("player_name", "UnknownPlayer")
                        game_id = st.session_state.get("game_id", "test_game")
                        
                        response = requests.post(
                            f"{BACKEND_URL}/game/{game_id}/vote",
                            json={"voter": my_name, "voted_for": execution_target},
                        )
                        response.raise_for_status()
                        st.toast(f"✅ {execution_target} 처형에 찬성했습니다.", icon="👍")
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "투표 실패")

            with col2:
                if st.button("👎 처형 반대", disabled=not execution_target):
                    try:
                        my_name = st.session_state.get("player_name", "UnknownPlayer")
                        game_id = st.session_state.get("game_id", "test_game")
                        
                        response = requests.post(
                            f"{BACKEND_URL}/game/{game_id}/vote",
                            json={"voter": my_name, "voted_for": None},
                        )
                        response.raise_for_status()
                        st.toast(f"✅ {execution_target} 처형에 반대했습니다.", icon="👎")
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "기권 처리 실패")
        elif phase == "night":
            my_role = st.session_state.get("my_role", "citizen")
            
            def use_ability(ability_name: str, ability_verb: str):
                if st.session_state.selection:
                    try:
                        my_name = st.session_state.get("player_name", "UnknownPlayer")
                        game_id = st.session_state.get("game_id", "test_game")
                        target_name = st.session_state.selection
                        
                        response = requests.post(
                            f"{BACKEND_URL}/game/{game_id}/ability",
                            json={"player_name": my_name, "ability": ability_name, "target": target_name}
                        )
                        response.raise_for_status()
                        
                        st.toast(f"✅ {target_name}을(를) {ability_verb} 대상으로 지정했습니다.", icon="🎯")
                        st.session_state.selection = None
                        st.rerun()
                    except requests.exceptions.RequestException as e:
                        handle_request_error(e, "능력 사용 실패")
                else:
                    st.warning("능력을 사용할 대상을 먼저 선택해주세요.")

            if my_role == "mafia":
                st.write("공격할 대상을 클릭하세요.")
                if st.button("공격 대상 확정", type="primary"):
                    use_ability("attack", "공격")
            elif my_role == "police":
                st.write("조사할 대상을 클릭하세요.")
                if st.button("조사 확정", type="primary"):
                    use_ability("investigate", "조사")
            elif my_role == "doctor":
                st.write("보호할 대상을 클릭하세요.")
                if st.button("보호 확정", type="primary"):
                    use_ability("protect", "보호")
            else:
                st.info("밤이 깊었습니다. 다른 플레이어들의 행동을 기다립니다.")
                st.button("대기 중...", disabled=True)
        else:
            st.write("대기 중...")

    # RAG Status and Debug Panel (Task G-12)
    st.divider()
    
    col1, col2 = st.columns([2, 3])
    with col1:
        st.caption("🌐 Server")
        if st.session_state.get("server_connected", False):
            st.markdown("![Connected](https://img.shields.io/badge/Status-Connected-brightgreen?style=flat-square)")
        else:
            st.markdown("![Disconnected](https://img.shields.io/badge/Status-Disconnected-red?style=flat-square)")
    
    with col2:
        st.caption("🧠 RAG")
        rag_status = st.session_state.get("rag_status", "unknown")
        if rag_status == "ok":
            st.markdown("![Active](https://img.shields.io/badge/RAG-Active-brightgreen?style=flat-square)")
        elif rag_status == "error":
            st.markdown("![Error](https://img.shields.io/badge/RAG-Error-red?style=flat-square)")
        else:
            st.markdown("![Unknown](https://img.shields.io/badge/RAG-Unknown-lightgrey?style=flat-square)")

    # LLM Provider Badge (Task G-16)
    provider = st.session_state.get("llm_provider", "unknown")
    provider_info = {
        "anthropic": {"label": "Anthropic Claude", "color": "blueviolet", "icon": "🟣"},
        "azure":     {"label": "Azure OpenAI", "color": "blue", "icon": "🔵"},
        "disabled":  {"label": "LLM Disabled", "color": "grey", "icon": "⚫"},
        "fallback":  {"label": "Fallback Mode", "color": "orange", "icon": "🟡"},
    }.get(provider, {"label": f"Unknown ({provider})", "color": "lightgrey", "icon": "❓"})

    st.caption(f"{provider_info['icon']} LLM Provider")
    st.markdown(f"![{provider}](https://img.shields.io/badge/LLM-{provider_info['label'].replace(' ', '%20')}-{provider_info['color']}?style=flat-square)")

    def _format_rag_hit(item: object) -> str:
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip()
            score = item.get("score")
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            title = str(meta.get("title") or meta.get("file") or "문서").strip() or "문서"
            score_s = f"{float(score):.4f}" if isinstance(score, (int, float)) else str(score)
            preview = text[:800] + ("…" if len(text) > 800 else "")
            return f"**{title}** (유사도 {score_s})\n\n{preview}"
        return str(item)

    with st.expander("🔍 RAG 컨텍스트 (디버그)"):
        rag_ctx = game_state.get("rag_context", [])
        if rag_ctx:
            for i, ctx in enumerate(rag_ctx):
                st.markdown(f"**{i + 1}.** {_format_rag_hit(ctx)}")
        else:
            st.caption("RAG 컨텍스트 없음 (AI 턴 이후 `game_state_update`에 포함됩니다)")

    with st.expander("🧠 AI 추론 미리보기 (관전·디버그)"):
        thoughts = game_state.get("agent_thoughts") or []
        if not thoughts:
            st.caption("아직 수신 없음 (`agent_thought` WS — `MAFIA_BROADCAST_AGENT_THOUGHTS=1` 기본)")
        else:
            for i, t in enumerate(reversed(thoughts[-20:])):
                if not isinstance(t, dict):
                    continue
                who = t.get("player_name") or t.get("agent_id", "?")
                ph = t.get("phase", "")
                rnd = t.get("round", "")
                cf = t.get("confidence")
                cf_s = f" · conf={float(cf):.2f}" if isinstance(cf, (int, float)) else ""
                st.markdown(f"**{who}** · {ph} R{rnd}{cf_s}")
                st.caption(str(t.get("reasoning_preview", ""))[:1200])

    with st.expander("🎛️ 슈퍼바이저 / MCP (디버그)"):
        directives = game_state.get("debug_directives", [])
        reports = game_state.get("debug_reports", [])
        if not directives and not reports:
            st.caption("지시문·보고 없음 (`report_to_supervisor` 및 Phase 진입 시 갱신)")
        if reports:
            st.markdown("**에이전트 → 슈퍼바이저 보고 (reports)**")
            for i, r in enumerate(reports):
                if isinstance(r, dict):
                    st.code(
                        f"[{i + 1}] round={r.get('round')} agent={r.get('agent_id')}\n{r.get('content', '')}",
                        language=None,
                    )
                else:
                    st.write(r)
        if directives:
            st.markdown("**슈퍼바이저 지시 (directives)**")
            for i, d in enumerate(directives):
                if isinstance(d, dict):
                    st.code(
                        f"[{i + 1}] → {d.get('target_agent')} ({d.get('type')}, {d.get('priority')})\n"
                        f"{d.get('content', '')}",
                        language=None,
                    )
                else:
                    st.write(d)

if __name__ == "__main__":
    st.session_state.game_state = {
        "phase": "낮", "round": 2, "timer_seconds": 134,
        "players": [
            {"name": "김민준", "is_alive": True},
            {"name": "박서연", "is_alive": True},
            {"name": "이지호", "is_alive": False},
            {"name": "최수아", "is_alive": True},
            {"name": "나", "is_alive": True},
        ],
        "rag_context": [
            "시민 추리 패턴: 첫날 어색하게 침묵하는 사람은 마피아일 확률이 있다.",
            "상황별 행동 사례: 8인 게임, 첫 낮에는 섣부른 지목보다 자유로운 대화로 정보를 얻는 것이 중요하다."
        ]
    }
    st.session_state.player_name = "나"
    st.session_state.rag_status = "ok"
    draw_status_panel()
