"""
HTTP-level tests for /api/v1/habits/* endpoints.
"""

from tests.conftest import get_auth_headers


class TestHabitsAuth:
    async def test_list_habits_requires_auth(self, client):
        response = await client.get("/api/v1/habits")
        assert response.status_code == 401

    async def test_create_habit_requires_auth(self, client):
        response = await client.post("/api/v1/habits", json={"name": "Run"})
        assert response.status_code == 401


class TestListHabits:
    async def test_list_habits_empty(self, client, make_user):
        user = await make_user()
        response = await client.get("/api/v1/habits", headers=get_auth_headers(user))
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_habits_returns_only_own(self, client, make_user, make_habit):
        user_a = await make_user()
        user_b = await make_user()
        await make_habit(user=user_a, name="Mine")
        await make_habit(user=user_b, name="Theirs")

        response = await client.get("/api/v1/habits", headers=get_auth_headers(user_a))
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["name"] == "Mine"


class TestCreateHabit:
    async def test_create_habit_returns_201(self, client, make_user):
        user = await make_user()
        response = await client.post(
            "/api/v1/habits",
            json={"name": "Meditate", "frequency": "daily"},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Meditate"
        assert body["frequency"] == "daily"
        assert str(body["user_id"]) == str(user.id)

    async def test_create_habit_missing_name_returns_422(self, client, make_user):
        user = await make_user()
        response = await client.post(
            "/api/v1/habits",
            json={"frequency": "daily"},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 422

    async def test_create_habit_defaults(self, client, make_user):
        user = await make_user()
        response = await client.post(
            "/api/v1/habits",
            json={"name": "Run"},
            headers=get_auth_headers(user),
        )
        body = response.json()
        assert body["target_days"] == [1, 2, 3, 4, 5, 6, 7]
        assert body["is_active"] is True


class TestGetHabit:
    async def test_get_habit_returns_200(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user, name="Yoga")

        response = await client.get(
            f"/api/v1/habits/{habit.id}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Yoga"

    async def test_get_habit_wrong_user_returns_404(
        self, client, make_user, make_habit
    ):
        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner, name="Yoga")

        response = await client.get(
            f"/api/v1/habits/{habit.id}",
            headers=get_auth_headers(other),
        )
        assert response.status_code == 404

    async def test_get_nonexistent_habit_returns_404(self, client, make_user):
        import uuid

        user = await make_user()
        response = await client.get(
            f"/api/v1/habits/{uuid.uuid4()}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 404


class TestUpdateHabit:
    async def test_update_habit_returns_200(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user, name="Old")

        response = await client.patch(
            f"/api/v1/habits/{habit.id}",
            json={"name": "New", "color": "#ff0000"},
            headers=get_auth_headers(user),
        )
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "New"
        assert body["color"] == "#ff0000"

    async def test_update_habit_wrong_user_returns_404(
        self, client, make_user, make_habit
    ):
        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner)

        response = await client.patch(
            f"/api/v1/habits/{habit.id}",
            json={"name": "Hacked"},
            headers=get_auth_headers(other),
        )
        assert response.status_code == 404


class TestDeleteHabit:
    async def test_delete_habit_returns_204(self, client, make_user, make_habit):
        user = await make_user()
        habit = await make_habit(user=user)

        response = await client.delete(
            f"/api/v1/habits/{habit.id}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 204

    async def test_delete_habit_wrong_user_returns_404(
        self, client, make_user, make_habit
    ):
        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner)

        response = await client.delete(
            f"/api/v1/habits/{habit.id}",
            headers=get_auth_headers(other),
        )
        assert response.status_code == 404

    async def test_delete_habit_then_get_returns_404(
        self, client, make_user, make_habit
    ):
        user = await make_user()
        habit = await make_habit(user=user)

        await client.delete(
            f"/api/v1/habits/{habit.id}",
            headers=get_auth_headers(user),
        )
        response = await client.get(
            f"/api/v1/habits/{habit.id}",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 404
