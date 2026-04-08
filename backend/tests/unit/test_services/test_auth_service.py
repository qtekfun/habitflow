"""
Tests for auth_service.py — written before implementation (TDD).

Covers:
- User registration (happy path + duplicate email)
- Login (happy path + wrong password + TOTP flow)
- TOTP setup, verify, disable
- Refresh token rotation
- Expired / invalid token handling
"""

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import generate_totp_secret


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_register_creates_user(self, db_session):
        from app.services.auth_service import register

        user = await register(
            db=db_session,
            email="alice@example.com",
            username="alice",
            password="Secret123!",
        )

        assert user.id is not None
        assert user.email == "alice@example.com"
        assert user.username == "alice"
        assert user.hashed_pass != "Secret123!"
        assert user.is_active is True
        assert user.totp_enabled is False

    async def test_register_duplicate_email_raises(self, db_session, make_user):
        from app.services.auth_service import register
        from app.services.auth_service import DuplicateEmailError

        await make_user(email="bob@example.com", username="bob")

        with pytest.raises(DuplicateEmailError):
            await register(
                db=db_session,
                email="bob@example.com",
                username="bob2",
                password="Secret123!",
            )

    async def test_register_duplicate_username_raises(self, db_session, make_user):
        from app.services.auth_service import register
        from app.services.auth_service import DuplicateUsernameError

        await make_user(email="carol@example.com", username="carol")

        with pytest.raises(DuplicateUsernameError):
            await register(
                db=db_session,
                email="carol2@example.com",
                username="carol",
                password="Secret123!",
            )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    async def test_login_returns_tokens(self, db_session, make_user):
        from app.services.auth_service import login

        user = await make_user(email="dave@example.com", username="dave", password="Pass1234!")
        result = await login(db=db_session, email="dave@example.com", password="Pass1234!")

        assert result["access_token"]
        assert result["refresh_token"]
        assert result.get("totp_required") is None

        # access token must decode correctly
        payload = jwt.decode(
            result["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "access"

    async def test_login_wrong_password_raises(self, db_session, make_user):
        from app.services.auth_service import login
        from app.services.auth_service import InvalidCredentialsError

        await make_user(email="eve@example.com", username="eve", password="Correct1!")

        with pytest.raises(InvalidCredentialsError):
            await login(db=db_session, email="eve@example.com", password="Wrong1234!")

    async def test_login_unknown_email_raises(self, db_session):
        from app.services.auth_service import login
        from app.services.auth_service import InvalidCredentialsError

        with pytest.raises(InvalidCredentialsError):
            await login(db=db_session, email="ghost@example.com", password="any")

    async def test_login_totp_enabled_returns_temp_token(self, db_session, make_user):
        from app.services.auth_service import login

        secret = generate_totp_secret()
        user = await make_user(
            email="frank@example.com",
            username="frank",
            password="Pass1234!",
            totp_enabled=True,
            totp_secret=secret,
        )
        result = await login(db=db_session, email="frank@example.com", password="Pass1234!")

        assert result["totp_required"] is True
        assert result["temp_token"]
        assert "access_token" not in result
        assert "refresh_token" not in result

        payload = jwt.decode(
            result["temp_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "temp"

    async def test_login_inactive_user_raises(self, db_session, make_user):
        from app.services.auth_service import login
        from app.services.auth_service import InvalidCredentialsError

        await make_user(email="inactive@example.com", username="inactive", password="Pass1!", is_active=False)

        with pytest.raises(InvalidCredentialsError):
            await login(db=db_session, email="inactive@example.com", password="Pass1!")


# ---------------------------------------------------------------------------
# TOTP second-factor login
# ---------------------------------------------------------------------------


class TestLoginTotp:
    async def test_totp_login_correct_code_returns_tokens(self, db_session, make_user):
        from app.services.auth_service import login, complete_totp_login
        import pyotp

        secret = generate_totp_secret()
        await make_user(
            email="gina@example.com",
            username="gina",
            password="Pass1234!",
            totp_enabled=True,
            totp_secret=secret,
        )
        step1 = await login(db=db_session, email="gina@example.com", password="Pass1234!")
        temp_token = step1["temp_token"]

        code = pyotp.TOTP(secret).now()
        result = await complete_totp_login(db=db_session, temp_token=temp_token, code=code)

        assert result["access_token"]
        assert result["refresh_token"]

    async def test_totp_login_wrong_code_raises(self, db_session, make_user):
        from app.services.auth_service import login, complete_totp_login
        from app.services.auth_service import InvalidTOTPError

        secret = generate_totp_secret()
        await make_user(
            email="harry@example.com",
            username="harry",
            password="Pass1234!",
            totp_enabled=True,
            totp_secret=secret,
        )
        step1 = await login(db=db_session, email="harry@example.com", password="Pass1234!")

        with pytest.raises(InvalidTOTPError):
            await complete_totp_login(
                db=db_session, temp_token=step1["temp_token"], code="000000"
            )

    async def test_totp_login_invalid_temp_token_raises(self, db_session):
        from app.services.auth_service import complete_totp_login
        from app.services.auth_service import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            await complete_totp_login(db=db_session, temp_token="not.a.token", code="123456")


# ---------------------------------------------------------------------------
# TOTP setup & verify
# ---------------------------------------------------------------------------


class TestTOTPSetup:
    async def test_totp_setup_generates_secret(self, db_session, make_user):
        from app.services.auth_service import setup_totp

        user = await make_user(email="iris@example.com", username="iris")
        result = await setup_totp(db=db_session, user=user)

        assert result["secret"]
        assert result["qr_uri"]
        assert "otpauth://" in result["qr_uri"]
        # secret persisted on user (not yet enabled)
        await db_session.refresh(user)
        assert user.totp_secret == result["secret"]
        assert user.totp_enabled is False

    async def test_totp_verify_activates_2fa(self, db_session, make_user):
        from app.services.auth_service import setup_totp, verify_totp_setup
        import pyotp

        user = await make_user(email="jake@example.com", username="jake")
        setup = await setup_totp(db=db_session, user=user)
        await db_session.refresh(user)

        code = pyotp.TOTP(setup["secret"]).now()
        await verify_totp_setup(db=db_session, user=user, code=code)

        await db_session.refresh(user)
        assert user.totp_enabled is True

    async def test_totp_verify_wrong_code_raises(self, db_session, make_user):
        from app.services.auth_service import setup_totp, verify_totp_setup
        from app.services.auth_service import InvalidTOTPError

        user = await make_user(email="kim@example.com", username="kim")
        await setup_totp(db=db_session, user=user)
        await db_session.refresh(user)

        with pytest.raises(InvalidTOTPError):
            await verify_totp_setup(db=db_session, user=user, code="000000")

    async def test_totp_disable(self, db_session, make_user):
        from app.services.auth_service import setup_totp, verify_totp_setup, disable_totp
        import pyotp

        user = await make_user(email="leo@example.com", username="leo")
        setup = await setup_totp(db=db_session, user=user)
        await db_session.refresh(user)
        code = pyotp.TOTP(setup["secret"]).now()
        await verify_totp_setup(db=db_session, user=user, code=code)
        await db_session.refresh(user)

        code2 = pyotp.TOTP(setup["secret"]).now()
        await disable_totp(db=db_session, user=user, code=code2)

        await db_session.refresh(user)
        assert user.totp_enabled is False
        assert user.totp_secret is None

    async def test_totp_disable_wrong_code_raises(self, db_session, make_user):
        from app.services.auth_service import setup_totp, verify_totp_setup, disable_totp
        from app.services.auth_service import InvalidTOTPError
        import pyotp

        user = await make_user(email="mia@example.com", username="mia")
        setup = await setup_totp(db=db_session, user=user)
        await db_session.refresh(user)
        code = pyotp.TOTP(setup["secret"]).now()
        await verify_totp_setup(db=db_session, user=user, code=code)
        await db_session.refresh(user)

        with pytest.raises(InvalidTOTPError):
            await disable_totp(db=db_session, user=user, code="000000")


# ---------------------------------------------------------------------------
# Refresh token rotation
# ---------------------------------------------------------------------------


class TestRefreshToken:
    async def test_refresh_token_rotation(self, db_session, make_user):
        from app.services.auth_service import login, refresh_tokens

        await make_user(email="nina@example.com", username="nina", password="Pass1!")
        tokens = await login(db=db_session, email="nina@example.com", password="Pass1!")
        old_rt = tokens["refresh_token"]

        new_tokens = await refresh_tokens(db=db_session, refresh_token=old_rt)

        assert new_tokens["access_token"]
        assert new_tokens["refresh_token"]
        # new refresh token must be different
        assert new_tokens["refresh_token"] != old_rt

    async def test_expired_refresh_token_raises(self, db_session):
        from app.services.auth_service import refresh_tokens
        from app.services.auth_service import InvalidTokenError
        from datetime import timedelta
        from app.core.security import create_refresh_token
        from unittest.mock import patch

        # Issue a refresh token that is immediately expired
        with patch(
            "app.core.security.timedelta",
            side_effect=lambda **kw: timedelta(seconds=-1),
        ):
            expired_rt = create_refresh_token(subject="00000000-0000-0000-0000-000000000000")

        with pytest.raises(InvalidTokenError):
            await refresh_tokens(db=db_session, refresh_token=expired_rt)

    async def test_invalid_refresh_token_raises(self, db_session):
        from app.services.auth_service import refresh_tokens
        from app.services.auth_service import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            await refresh_tokens(db=db_session, refresh_token="garbage.token.value")

    async def test_refresh_token_wrong_type_raises(self, db_session, make_user):
        """Using an access token as a refresh token must fail."""
        from app.services.auth_service import refresh_tokens, login
        from app.services.auth_service import InvalidTokenError

        await make_user(email="oscar@example.com", username="oscar", password="Pass1!")
        tokens = await login(db=db_session, email="oscar@example.com", password="Pass1!")
        access_token = tokens["access_token"]

        with pytest.raises(InvalidTokenError):
            await refresh_tokens(db=db_session, refresh_token=access_token)
