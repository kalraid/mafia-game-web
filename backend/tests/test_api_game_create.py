from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_post_game_create_success() -> None:
    client = TestClient(app)
    resp = client.post(
        "/game/create",
        json={"host_name": "호스트A", "player_count": 8},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["player_count"] == 8
    assert data["game_id"].startswith("g_")
    assert len(data["game_id"]) > len("g_")


def test_post_game_create_validation_player_count_low() -> None:
    client = TestClient(app)
    resp = client.post(
        "/game/create",
        json={"host_name": "a", "player_count": 3},
    )
    assert resp.status_code == 422


def test_post_game_create_validation_player_count_high() -> None:
    client = TestClient(app)
    resp = client.post(
        "/game/create",
        json={"host_name": "a", "player_count": 21},
    )
    assert resp.status_code == 422


def test_post_game_create_validation_host_name_empty() -> None:
    client = TestClient(app)
    resp = client.post(
        "/game/create",
        json={"host_name": "", "player_count": 8},
    )
    assert resp.status_code == 422


def test_post_chat_unknown_game_returns_404() -> None:
    client = TestClient(app)
    resp = client.post(
        "/game/does_not_exist_zzzz/chat",
        json={"sender": "p", "content": "hi", "channel": "global"},
    )
    assert resp.status_code == 404


def test_health_includes_rag_status() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["rag_status"] in ("ok", "error", "unknown")
    assert data["llm_provider"] in ("anthropic", "azure", "disabled", "fallback")
