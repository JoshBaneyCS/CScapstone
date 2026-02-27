"""Tests for Blackjack API session isolation and game logic."""
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


class TestGameFlow:
    """Test basic blackjack game flow."""

    def test_start_game(self):
        resp = client.post(
            "/blackjack/start",
            json={"bet": 100},
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("in_progress", "player_win", "dealer_win", "push")
        assert len(data["player_hand"]) == 2
        assert len(data["dealer_hand"]) == 2
        assert data["bet"] == 100

    def test_hit(self):
        client.post("/blackjack/start", json={"bet": 50}, headers={"X-User-ID": "user-1"})
        resp = client.post("/blackjack/hit", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["player_hand"]) >= 3

    def test_stand(self):
        client.post("/blackjack/start", json={"bet": 50}, headers={"X-User-ID": "user-1"})
        resp = client.post("/blackjack/stand", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("player_win", "dealer_win", "dealer_bust", "push")

    def test_get_state(self):
        client.post("/blackjack/start", json={"bet": 75}, headers={"X-User-ID": "user-1"})
        resp = client.get("/blackjack/state", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 200
        assert resp.json()["bet"] == 75

    def test_invalid_bet(self):
        resp = client.post(
            "/blackjack/start",
            json={"bet": 0},
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 400

    def test_hit_without_start(self):
        resp = client.post("/blackjack/hit", headers={"X-User-ID": "no-game-user"})
        assert resp.status_code == 400

    def test_stand_without_start(self):
        resp = client.post("/blackjack/stand", headers={"X-User-ID": "no-game-user"})
        assert resp.status_code == 400

    def test_state_without_start(self):
        resp = client.get("/blackjack/state", headers={"X-User-ID": "no-game-user"})
        assert resp.status_code == 400


class TestSessionIsolation:
    """Test that different users get independent game sessions."""

    def test_two_users_independent_bets(self):
        """Two users start games with different bets — each should see their own bet."""
        r1 = client.post("/blackjack/start", json={"bet": 50}, headers={"X-User-ID": "user-1"})
        r2 = client.post("/blackjack/start", json={"bet": 75}, headers={"X-User-ID": "user-2"})
        assert r1.status_code == 200
        assert r2.status_code == 200

        s1 = client.get("/blackjack/state", headers={"X-User-ID": "user-1"})
        s2 = client.get("/blackjack/state", headers={"X-User-ID": "user-2"})
        assert s1.json()["bet"] == 50
        assert s2.json()["bet"] == 75

    def test_no_cross_contamination(self):
        """User 2 starting a game must not affect user 1's hands."""
        r1 = client.post("/blackjack/start", json={"bet": 10}, headers={"X-User-ID": "iso-1"})
        hands_before = r1.json()["player_hand"]

        # User 2 starts their own game
        client.post("/blackjack/start", json={"bet": 20}, headers={"X-User-ID": "iso-2"})

        # User 1's hand must be unchanged
        r1_after = client.get("/blackjack/state", headers={"X-User-ID": "iso-1"})
        assert r1_after.json()["player_hand"] == hands_before

    def test_user2_hit_doesnt_affect_user1(self):
        """User 2 hitting should not change user 1's game."""
        client.post("/blackjack/start", json={"bet": 10}, headers={"X-User-ID": "user-a"})
        client.post("/blackjack/start", json={"bet": 20}, headers={"X-User-ID": "user-b"})

        state_a_before = client.get("/blackjack/state", headers={"X-User-ID": "user-a"}).json()

        # User B hits
        client.post("/blackjack/hit", headers={"X-User-ID": "user-b"})

        state_a_after = client.get("/blackjack/state", headers={"X-User-ID": "user-a"}).json()
        assert state_a_after["player_hand"] == state_a_before["player_hand"]
        assert state_a_after["dealer_hand"] == state_a_before["dealer_hand"]

    def test_many_users(self):
        """10 users can each have independent games."""
        for i in range(10):
            resp = client.post(
                "/blackjack/start",
                json={"bet": (i + 1) * 10},
                headers={"X-User-ID": f"user-{i}"},
            )
            assert resp.status_code == 200

        # Verify each user has their own bet
        for i in range(10):
            state = client.get("/blackjack/state", headers={"X-User-ID": f"user-{i}"}).json()
            assert state["bet"] == (i + 1) * 10

    def test_user_restart_overwrites_own_session(self):
        """A user starting a new game should overwrite only their own session."""
        client.post("/blackjack/start", json={"bet": 10}, headers={"X-User-ID": "restart-user"})
        client.post("/blackjack/start", json={"bet": 99}, headers={"X-User-ID": "restart-user"})

        state = client.get("/blackjack/state", headers={"X-User-ID": "restart-user"}).json()
        assert state["bet"] == 99
