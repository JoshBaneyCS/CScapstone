"""Tests for Poker API session isolation and game logic."""
import pytest
from fastapi.testclient import TestClient

from main import app, SESSIONS

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before each test."""
    SESSIONS.clear()
    yield
    SESSIONS.clear()


DEFAULT_START = {
    "player_bankroll": 100,
    "cpu_bankroll": 100,
    "cpu_players": 2,
    "bet": 10,
}


class TestGameFlow:
    """Test basic poker game flow."""

    def test_single_start(self):
        resp = client.post(
            "/texas/single/start",
            json=DEFAULT_START,
            headers={"X-User-ID": "poker-1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "Player" in data["players_hands"]
        assert data["mode"] == "single"
        assert data["bet"] == 10
        assert data["status"] == "preflop"

    def test_player_action_stay(self):
        client.post("/texas/single/start", json=DEFAULT_START, headers={"X-User-ID": "poker-1"})
        resp = client.post(
            "/texas/single/action",
            json={"action": "stay", "amount": 0},
            headers={"X-User-ID": "poker-1"},
        )
        assert resp.status_code == 200

    def test_player_action_fold(self):
        client.post("/texas/single/start", json=DEFAULT_START, headers={"X-User-ID": "poker-1"})
        resp = client.post(
            "/texas/single/action",
            json={"action": "fold", "amount": 0},
            headers={"X-User-ID": "poker-1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "finished"

    def test_get_state(self):
        client.post("/texas/single/start", json=DEFAULT_START, headers={"X-User-ID": "poker-1"})
        resp = client.get("/texas/state", headers={"X-User-ID": "poker-1"})
        assert resp.status_code == 200
        assert resp.json()["bet"] == 10

    def test_action_without_start(self):
        resp = client.post(
            "/texas/single/action",
            json={"action": "stay", "amount": 0},
            headers={"X-User-ID": "no-game-user"},
        )
        assert resp.status_code == 400

    def test_state_without_start(self):
        resp = client.get("/texas/state", headers={"X-User-ID": "no-game-user"})
        assert resp.status_code == 400


class TestSessionIsolation:
    """Test that different users get independent poker sessions."""

    def test_two_users_independent_bets(self):
        """Two users start games with different configs — each sees their own."""
        r1 = client.post(
            "/texas/single/start",
            json={**DEFAULT_START, "bet": 10},
            headers={"X-User-ID": "poker-iso-1"},
        )
        r2 = client.post(
            "/texas/single/start",
            json={**DEFAULT_START, "bet": 20},
            headers={"X-User-ID": "poker-iso-2"},
        )
        assert r1.status_code == 200
        assert r2.status_code == 200

        s1 = client.get("/texas/state", headers={"X-User-ID": "poker-iso-1"})
        s2 = client.get("/texas/state", headers={"X-User-ID": "poker-iso-2"})
        assert s1.json()["bet"] == 10
        assert s2.json()["bet"] == 20

    def test_no_cross_contamination(self):
        """User 2 starting a game must not affect user 1's hands."""
        r1 = client.post(
            "/texas/single/start",
            json=DEFAULT_START,
            headers={"X-User-ID": "iso-1"},
        )
        hands_before = r1.json()["players_hands"]["Player"]

        # User 2 starts their own game
        client.post(
            "/texas/single/start",
            json=DEFAULT_START,
            headers={"X-User-ID": "iso-2"},
        )

        # User 1's hand must be unchanged
        r1_after = client.get("/texas/state", headers={"X-User-ID": "iso-1"})
        assert r1_after.json()["players_hands"]["Player"] == hands_before

    def test_user2_action_doesnt_affect_user1(self):
        """User 2's action should not change user 1's game."""
        client.post("/texas/single/start", json=DEFAULT_START, headers={"X-User-ID": "user-a"})
        client.post("/texas/single/start", json=DEFAULT_START, headers={"X-User-ID": "user-b"})

        state_a_before = client.get("/texas/state", headers={"X-User-ID": "user-a"}).json()

        # User B takes an action
        client.post(
            "/texas/single/action",
            json={"action": "stay", "amount": 0},
            headers={"X-User-ID": "user-b"},
        )

        state_a_after = client.get("/texas/state", headers={"X-User-ID": "user-a"}).json()
        assert state_a_after["players_hands"]["Player"] == state_a_before["players_hands"]["Player"]

    def test_many_users(self):
        """5 users can each have independent games."""
        for i in range(5):
            resp = client.post(
                "/texas/single/start",
                json={**DEFAULT_START, "bet": (i + 1) * 5},
                headers={"X-User-ID": f"poker-{i}"},
            )
            assert resp.status_code == 200

        # Verify each user has their own bet
        for i in range(5):
            state = client.get("/texas/state", headers={"X-User-ID": f"poker-{i}"}).json()
            assert state["bet"] == (i + 1) * 5
