"""
HTTP-level tests for /api/v1/logs/* endpoints.
"""

from datetime import date

from tests.conftest import days_ago, get_auth_headers


class TestCheckin:
    async def test_checkin_returns_201(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user)

        response = await client.post(
            "/api/v1/logs",
            json={"habit_id": str(habit.id), "log_date": str(date.today())},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["habit_id"] == str(habit.id)
        assert body["completed"] is True

    async def test_checkin_with_note(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user)

        response = await client.post(
            "/api/v1/logs",
            json={
                "habit_id": str(habit.id),
                "log_date": str(date.today()),
                "note": "Felt great!",
            },
            headers=get_auth_headers(user),
        )
        assert response.status_code == 201
        assert response.json()["note"] == "Felt great!"

    async def test_checkin_duplicate_returns_409(
        self, client, make_user, make_habit, make_log
    ):
        user = await make_user()
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=date.today())

        response = await client.post(
            "/api/v1/logs",
            json={"habit_id": str(habit.id), "log_date": str(date.today())},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 409

    async def test_checkin_other_users_habit_returns_404(
        self, client, make_user, make_habit
    ):
        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner)

        response = await client.post(
            "/api/v1/logs",
            json={"habit_id": str(habit.id), "log_date": str(date.today())},
            headers=get_auth_headers(other),
        )
        assert response.status_code == 404

    async def test_checkin_requires_auth(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user)
        response = await client.post(
            "/api/v1/logs",
            json={"habit_id": str(habit.id), "log_date": str(date.today())},
        )
        assert response.status_code == 401


class TestUndoCheckin:
    async def test_undo_returns_204(self, client, make_user, make_habit, make_log):
        user = await make_user()
        habit = await make_habit(user=user)
        log = await make_log(habit=habit, user=user, log_date=date.today())

        response = await client.delete(
            f"/api/v1/logs/{log.id}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 204

    async def test_undo_wrong_user_returns_404(
        self, client, make_user, make_habit, make_log
    ):
        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner)
        log = await make_log(habit=habit, user=owner, log_date=date.today())

        response = await client.delete(
            f"/api/v1/logs/{log.id}",
            headers=get_auth_headers(other),
        )
        assert response.status_code == 404

    async def test_undo_requires_auth(self, client, make_user, make_habit, make_log):
        user = await make_user()
        habit = await make_habit(user=user)
        log = await make_log(habit=habit, user=user, log_date=date.today())

        response = await client.delete(f"/api/v1/logs/{log.id}")
        assert response.status_code == 401


class TestToday:
    async def test_today_requires_auth(self, client):
        response = await client.get("/api/v1/logs/today")
        assert response.status_code == 401

    async def test_today_returns_all_active_habits(self, client, make_user, make_habit):
        user = await make_user()
        await make_habit(user=user, name="Run")
        await make_habit(user=user, name="Read")
        await make_habit(user=user, name="Inactive", is_active=False)

        response = await client.get(
            "/api/v1/logs/today",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 200
        body = response.json()
        names = {r["name"] for r in body}
        assert "Run" in names
        assert "Read" in names
        assert "Inactive" not in names

    async def test_today_marks_completed(self, client, make_user, make_habit, make_log):
        user = await make_user()
        habit = await make_habit(user=user, name="Run")
        await make_log(habit=habit, user=user, log_date=date.today())

        response = await client.get(
            "/api/v1/logs/today",
            headers=get_auth_headers(user),
        )
        entry = next(r for r in response.json() if r["name"] == "Run")
        assert entry["completed"] is True


class TestStats:
    async def test_stats_requires_auth(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user)
        response = await client.get(
            f"/api/v1/logs/stats?habit_id={habit.id}&from_date={days_ago(6)}&to_date={date.today()}"
        )
        assert response.status_code == 401

    async def test_stats_returns_expected_keys(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user)

        response = await client.get(
            f"/api/v1/logs/stats?habit_id={habit.id}&from_date={days_ago(6)}&to_date={date.today()}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 200
        body = response.json()
        assert "total_days" in body
        assert "completed_days" in body
        assert "completion_rate" in body
        assert "weekly_average" in body

    async def test_stats_wrong_habit_returns_404(self, client, make_user, make_habit):
        import uuid

        user = await make_user()
        response = await client.get(
            f"/api/v1/logs/stats?habit_id={uuid.uuid4()}&from_date={days_ago(6)}&to_date={date.today()}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 404
