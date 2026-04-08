"""
Integration tests — full user journeys exercised end-to-end via HTTP.

Each test drives the API the same way a real client would:
register → login → act → assert.
No direct DB manipulation; only the `client` fixture and HTTP calls.
"""

from datetime import date

import pyotp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def register_and_login(client, email: str, username: str, password: str) -> str:
    """Register a user and return their access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Flow 1: Register → Login → Create habit → Check-in → Streak
# ---------------------------------------------------------------------------


class TestHabitCheckinStreakFlow:
    async def test_full_daily_streak_flow(self, client):
        """
        Register → login → create habit → check-in today
        → GET habit/{id} shows current_streak = 1.
        """
        token = await register_and_login(
            client, "streak@example.com", "streakuser", "Test1234!"
        )

        # Create habit
        create_resp = await client.post(
            "/api/v1/habits",
            json={"name": "Meditate", "frequency": "daily"},
            headers=auth(token),
        )
        assert create_resp.status_code == 201
        habit_id = create_resp.json()["id"]

        # Check in today
        checkin_resp = await client.post(
            "/api/v1/logs",
            json={"habit_id": habit_id, "log_date": str(date.today())},
            headers=auth(token),
        )
        assert checkin_resp.status_code == 201

        # Verify streak in habit detail
        detail_resp = await client.get(
            f"/api/v1/habits/{habit_id}", headers=auth(token)
        )
        assert detail_resp.status_code == 200
        body = detail_resp.json()
        assert body["current_streak"] == 1
        assert body["longest_streak"] == 1

    async def test_today_endpoint_reflects_checkin(self, client):
        """Check-in via POST /logs then GET /logs/today shows completed=True."""
        token = await register_and_login(
            client, "today@example.com", "todayuser", "Test1234!"
        )

        create_resp = await client.post(
            "/api/v1/habits",
            json={"name": "Run"},
            headers=auth(token),
        )
        habit_id = create_resp.json()["id"]

        # Before check-in
        today_resp = await client.get("/api/v1/logs/today", headers=auth(token))
        entry = next(r for r in today_resp.json() if r["habit_id"] == habit_id)
        assert entry["completed"] is False

        # Check in
        await client.post(
            "/api/v1/logs",
            json={"habit_id": habit_id, "log_date": str(date.today())},
            headers=auth(token),
        )

        # After check-in
        today_resp2 = await client.get("/api/v1/logs/today", headers=auth(token))
        entry2 = next(r for r in today_resp2.json() if r["habit_id"] == habit_id)
        assert entry2["completed"] is True

    async def test_undo_checkin_flow(self, client):
        """Check-in → undo → today shows completed=False again."""
        token = await register_and_login(
            client, "undo@example.com", "undouser", "Test1234!"
        )
        create_resp = await client.post(
            "/api/v1/habits", json={"name": "Yoga"}, headers=auth(token)
        )
        habit_id = create_resp.json()["id"]

        checkin_resp = await client.post(
            "/api/v1/logs",
            json={"habit_id": habit_id, "log_date": str(date.today())},
            headers=auth(token),
        )
        log_id = checkin_resp.json()["id"]

        # Undo
        undo_resp = await client.delete(f"/api/v1/logs/{log_id}", headers=auth(token))
        assert undo_resp.status_code == 204

        # Streak back to 0
        detail_resp = await client.get(
            f"/api/v1/habits/{habit_id}", headers=auth(token)
        )
        assert detail_resp.json()["current_streak"] == 0

    async def test_stats_flow(self, client):
        """Check-in 3 of 7 days → stats shows completion_rate ≈ 3/7."""
        token = await register_and_login(
            client, "stats@example.com", "statsuser", "Test1234!"
        )
        create_resp = await client.post(
            "/api/v1/habits", json={"name": "Read"}, headers=auth(token)
        )
        habit_id = create_resp.json()["id"]

        # Log days 0, 2, 4 (3 days out of 7)
        for days_back in [0, 2, 4]:
            log_date = str(date.fromordinal(date.today().toordinal() - days_back))
            await client.post(
                "/api/v1/logs",
                json={"habit_id": habit_id, "log_date": log_date},
                headers=auth(token),
            )

        from_date = str(date.fromordinal(date.today().toordinal() - 6))
        stats_resp = await client.get(
            f"/api/v1/logs/stats?habit_id={habit_id}&from_date={from_date}&to_date={date.today()}",
            headers=auth(token),
        )
        assert stats_resp.status_code == 200
        body = stats_resp.json()
        assert body["completed_days"] == 3
        assert body["total_days"] == 7
        assert abs(body["completion_rate"] - 3 / 7) < 0.001


# ---------------------------------------------------------------------------
# Flow 2: Token refresh flow
# ---------------------------------------------------------------------------


class TestTokenRefreshFlow:
    async def test_refresh_gives_new_access_token(self, client):
        """Login → use refresh cookie → get new access token → still authenticated."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "username": "refreshuser",
                "password": "Test1234!",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "Test1234!"},
        )
        old_token = login_resp.json()["access_token"]
        refresh_cookie = login_resp.cookies["refresh_token"]

        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_cookie},
        )
        assert refresh_resp.status_code == 200
        new_token = refresh_resp.json()["access_token"]
        assert new_token  # non-empty

        # New token is valid for authenticated requests
        habits_resp = await client.get("/api/v1/habits", headers=auth(new_token))
        assert habits_resp.status_code == 200

        # Old token also still valid (access tokens are stateless JWTs)
        habits_resp2 = await client.get("/api/v1/habits", headers=auth(old_token))
        assert habits_resp2.status_code == 200


# ---------------------------------------------------------------------------
# Flow 3: TOTP setup and login
# ---------------------------------------------------------------------------


class TestTOTPFlow:
    async def test_totp_setup_and_login_flow(self, client):
        """
        Register → login → setup TOTP → verify TOTP (enable 2FA)
        → logout → login again → TOTP challenge → submit code → authenticated.
        """
        # Register and login (no 2FA yet)
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "totp_flow@example.com",
                "username": "totpflow",
                "password": "Test1234!",
            },
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "totp_flow@example.com", "password": "Test1234!"},
        )
        token = login_resp.json()["access_token"]

        # Setup TOTP
        setup_resp = await client.post("/api/v1/auth/totp/setup", headers=auth(token))
        assert setup_resp.status_code == 200
        secret = setup_resp.json()["secret"]

        # Verify with valid code (enables 2FA)
        code = pyotp.TOTP(secret).now()
        verify_resp = await client.post(
            "/api/v1/auth/totp/verify",
            json={"code": code},
            headers=auth(token),
        )
        assert verify_resp.status_code == 200

        # Logout
        await client.post("/api/v1/auth/logout", headers=auth(token))

        # Login again — should get TOTP challenge
        login2_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "totp_flow@example.com", "password": "Test1234!"},
        )
        assert login2_resp.status_code == 200
        assert login2_resp.json()["totp_required"] is True
        temp_token = login2_resp.json()["temp_token"]

        # Complete TOTP login
        totp_code = pyotp.TOTP(secret).now()
        totp_resp = await client.post(
            "/api/v1/auth/login/totp",
            json={"temp_token": temp_token, "code": totp_code},
        )
        assert totp_resp.status_code == 200
        final_token = totp_resp.json()["access_token"]

        # Final token is valid
        habits_resp = await client.get("/api/v1/habits", headers=auth(final_token))
        assert habits_resp.status_code == 200


# ---------------------------------------------------------------------------
# Flow 4: Multi-user isolation
# ---------------------------------------------------------------------------


class TestMultiUserIsolation:
    async def test_users_cannot_see_each_others_habits(self, client):
        """User A's habits are not visible to User B."""
        token_a = await register_and_login(
            client, "user_a@example.com", "user_a", "Test1234!"
        )
        token_b = await register_and_login(
            client, "user_b@example.com", "user_b", "Test1234!"
        )

        # A creates a habit
        create_resp = await client.post(
            "/api/v1/habits",
            json={"name": "Secret habit"},
            headers=auth(token_a),
        )
        habit_id = create_resp.json()["id"]

        # B cannot see it in their list
        list_resp = await client.get("/api/v1/habits", headers=auth(token_b))
        habit_ids = [h["id"] for h in list_resp.json()]
        assert habit_id not in habit_ids

        # B cannot get it by ID
        detail_resp = await client.get(
            f"/api/v1/habits/{habit_id}", headers=auth(token_b)
        )
        assert detail_resp.status_code == 404

    async def test_users_cannot_checkin_each_others_habits(self, client):
        """User B cannot check-in on User A's habit."""
        token_a = await register_and_login(
            client, "iso_a@example.com", "iso_a", "Test1234!"
        )
        token_b = await register_and_login(
            client, "iso_b@example.com", "iso_b", "Test1234!"
        )

        create_resp = await client.post(
            "/api/v1/habits",
            json={"name": "A only"},
            headers=auth(token_a),
        )
        habit_id = create_resp.json()["id"]

        checkin_resp = await client.post(
            "/api/v1/logs",
            json={"habit_id": habit_id, "log_date": str(date.today())},
            headers=auth(token_b),
        )
        assert checkin_resp.status_code == 404

    async def test_delete_habit_removes_logs(self, client):
        """Deleting a habit cascades — logs/today no longer shows it."""
        token = await register_and_login(
            client, "cascade@example.com", "cascadeuser", "Test1234!"
        )

        create_resp = await client.post(
            "/api/v1/habits", json={"name": "Temp"}, headers=auth(token)
        )
        habit_id = create_resp.json()["id"]

        await client.post(
            "/api/v1/logs",
            json={"habit_id": habit_id, "log_date": str(date.today())},
            headers=auth(token),
        )

        # Delete habit
        del_resp = await client.delete(
            f"/api/v1/habits/{habit_id}", headers=auth(token)
        )
        assert del_resp.status_code == 204

        # No longer in today's list
        today_resp = await client.get("/api/v1/logs/today", headers=auth(token))
        ids = [r["habit_id"] for r in today_resp.json()]
        assert habit_id not in ids
