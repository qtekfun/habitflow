"""
HTTP-level tests for /api/v1/auth/* endpoints.

Uses the `client` fixture (AsyncClient + test DB) from conftest.
"""

from tests.conftest import get_auth_headers


class TestRegister:
    async def test_register_returns_201(self, client, make_user):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "username": "newuser",
                "password": "Test1234!",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "new@example.com"
        assert body["username"] == "newuser"
        assert "hashed_pass" not in body

    async def test_register_duplicate_email_returns_409(self, client, make_user):
        user = await make_user(email="dup@example.com")
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": user.email, "username": "other", "password": "Test1234!"},
        )
        assert response.status_code == 409

    async def test_register_duplicate_username_returns_409(self, client, make_user):
        user = await make_user(username="taken")
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "username": user.username,
                "password": "Test1234!",
            },
        )
        assert response.status_code == 409

    async def test_register_invalid_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "username": "user", "password": "Test1234!"},
        )
        assert response.status_code == 422

    async def test_register_missing_fields_returns_422(self, client):
        response = await client.post("/api/v1/auth/register", json={"email": "a@b.com"})
        assert response.status_code == 422


class TestLogin:
    async def test_login_returns_access_token(self, client, make_user):
        await make_user(email="login@example.com", password="Secret1!")
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "Secret1!"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_sets_refresh_cookie(self, client, make_user):
        await make_user(email="cookie@example.com", password="Secret1!")
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "cookie@example.com", "password": "Secret1!"},
        )
        assert "refresh_token" in response.cookies

    async def test_login_wrong_password_returns_401(self, client, make_user):
        await make_user(email="wrong@example.com", password="Correct1!")
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "Wrong1!"},
        )
        assert response.status_code == 401

    async def test_login_unknown_email_returns_401(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Test1234!"},
        )
        assert response.status_code == 401

    async def test_login_totp_user_returns_temp_token(self, client, make_user):
        await make_user(
            email="totp@example.com",
            password="Secret1!",
            totp_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "totp@example.com", "password": "Secret1!"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["totp_required"] is True
        assert "temp_token" in body


class TestTOTPLogin:
    async def test_totp_login_invalid_code_returns_401(self, client, make_user):
        await make_user(
            email="totp2@example.com",
            password="Secret1!",
            totp_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",
        )
        # Get a temp token first
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "totp2@example.com", "password": "Secret1!"},
        )
        temp_token = login_resp.json()["temp_token"]

        response = await client.post(
            "/api/v1/auth/login/totp",
            json={"temp_token": temp_token, "code": "000000"},
        )
        assert response.status_code == 401


class TestRefresh:
    async def test_refresh_returns_new_access_token(self, client, make_user):
        from app.core.security import create_refresh_token

        user = await make_user()
        refresh = create_refresh_token(subject=str(user.id))

        response = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_refresh_without_cookie_returns_401(self, client):
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_rotates_cookie(self, client, make_user):
        from app.core.security import create_refresh_token

        user = await make_user()
        refresh = create_refresh_token(subject=str(user.id))

        response = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh},
        )
        assert "refresh_token" in response.cookies


class TestLogout:
    async def test_logout_clears_cookie(self, client, make_user):
        user = await make_user()
        response = await client.post(
            "/api/v1/auth/logout",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 200
        # Cookie should be cleared (max-age=0 or empty value)
        cookie = response.cookies.get("refresh_token", "")
        assert cookie == ""


class TestTOTPSetup:
    async def test_totp_setup_requires_auth(self, client):
        response = await client.post("/api/v1/auth/totp/setup")
        assert response.status_code == 401

    async def test_totp_setup_returns_secret_and_qr(self, client, make_user):
        user = await make_user()
        response = await client.post(
            "/api/v1/auth/totp/setup",
            headers=get_auth_headers(user),
        )
        assert response.status_code == 200
        body = response.json()
        assert "secret" in body
        assert "qr_uri" in body

    async def test_totp_disable_requires_auth(self, client):
        response = await client.delete("/api/v1/auth/totp")
        assert response.status_code == 401
