"""
Authentication service.

Responsibilities:
- User registration (email + username uniqueness)
- Login: returns tokens or TOTP challenge
- TOTP second-factor completion
- TOTP setup, verify, disable
- Refresh token rotation
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    verify_password,
    verify_totp,
)
from app.models.user import User


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------


class DuplicateEmailError(Exception):
    pass


class DuplicateUsernameError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidTOTPError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def register(
    *,
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
) -> User:
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise DuplicateEmailError(f"Email already registered: {email}")

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none() is not None:
        raise DuplicateUsernameError(f"Username already taken: {username}")

    user = User(
        email=email,
        username=username,
        hashed_pass=hash_password(password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def login(
    *,
    db: AsyncSession,
    email: str,
    password: str,
) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user: User | None = result.scalar_one_or_none()

    if user is None or not user.is_active or not verify_password(password, user.hashed_pass):
        raise InvalidCredentialsError("Invalid email or password")

    if user.totp_enabled:
        return {
            "totp_required": True,
            "temp_token": create_temp_token(subject=str(user.id)),
        }

    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
    }


# ---------------------------------------------------------------------------
# TOTP second-factor
# ---------------------------------------------------------------------------


async def complete_totp_login(
    *,
    db: AsyncSession,
    temp_token: str,
    code: str,
) -> dict:
    try:
        payload = decode_token(temp_token)
    except Exception as exc:
        raise InvalidTokenError("Invalid or expired temp token") from exc

    if payload.get("type") != "temp":
        raise InvalidTokenError("Token is not a temp token")

    user_id: str = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None or not user.totp_secret:
        raise InvalidCredentialsError("User not found or TOTP not configured")

    if not verify_totp(user.totp_secret, code):
        raise InvalidTOTPError("Invalid TOTP code")

    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
    }


# ---------------------------------------------------------------------------
# TOTP management
# ---------------------------------------------------------------------------


async def setup_totp(*, db: AsyncSession, user: User) -> dict:
    secret = generate_totp_secret()
    user.totp_secret = secret
    db.add(user)
    await db.flush()
    return {
        "secret": secret,
        "qr_uri": get_totp_uri(secret, user.email),
    }


async def verify_totp_setup(*, db: AsyncSession, user: User, code: str) -> None:
    if not user.totp_secret or not verify_totp(user.totp_secret, code):
        raise InvalidTOTPError("Invalid TOTP code")
    user.totp_enabled = True
    db.add(user)
    await db.flush()


async def disable_totp(*, db: AsyncSession, user: User, code: str) -> None:
    if not user.totp_secret or not verify_totp(user.totp_secret, code):
        raise InvalidTOTPError("Invalid TOTP code")
    user.totp_enabled = False
    user.totp_secret = None
    db.add(user)
    await db.flush()


# ---------------------------------------------------------------------------
# Refresh token rotation
# ---------------------------------------------------------------------------


async def refresh_tokens(*, db: AsyncSession, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise InvalidTokenError("Invalid or expired refresh token") from exc

    if payload.get("type") != "refresh":
        raise InvalidTokenError("Token is not a refresh token")

    user_id: str = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise InvalidTokenError("User not found or inactive")

    return {
        "access_token": create_access_token(subject=str(user.id)),
        "refresh_token": create_refresh_token(subject=str(user.id)),
    }
