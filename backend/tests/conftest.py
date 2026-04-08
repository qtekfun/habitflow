"""
Test fixtures for HabitFlow backend.

Provides:
- Async test database (isolated from production)
- AsyncClient fixture (httpx)
- Factory fixtures: make_user(), make_habit(), make_log()
- Auth helper: get_auth_headers(user)
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.user import User

# ---------------------------------------------------------------------------
# Import all models so their tables are registered on Base.metadata
# ---------------------------------------------------------------------------
import app.models.user  # noqa: F401
import app.models.habit  # noqa: F401
import app.models.habit_log  # noqa: F401

# ---------------------------------------------------------------------------
# Lazy import of the FastAPI app — avoids circular import issues during
# collection phase while still allowing the app to initialise normally.
# ---------------------------------------------------------------------------


def _get_app():
    from app.main import app  # noqa: PLC0415

    return app


# ---------------------------------------------------------------------------
# Test database engine
# ---------------------------------------------------------------------------

test_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    echo=False,
    # NullPool: every connect() opens a fresh connection in the current event
    # loop — avoids "Future attached to a different loop" with pytest-asyncio.
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Schema lifecycle — synchronous fixture so it never touches the async loop
# used by function-scoped fixtures. asyncio.run() spins its own temporary
# loop for the DDL statements, then exits cleanly.
# ---------------------------------------------------------------------------


async def _create_tables() -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await test_engine.dispose()


async def _drop_tables() -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_tables())


# ---------------------------------------------------------------------------
# Per-test database session with automatic rollback
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an AsyncSession that is rolled back after each test, keeping
    the test database clean without the overhead of re-creating tables.

    Uses TestSessionLocal() directly (no bind=conn) to avoid cross-loop
    Future issues with asyncpg under pytest-asyncio 0.24+.
    Services call flush() but never commit(), so rollback() cleanly undoes
    all changes made during the test.
    """
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI AsyncClient wired to the test DB
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Returns an httpx AsyncClient that targets the FastAPI app with the
    test database session injected via dependency override.
    """
    app = _get_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def make_user(db_session: AsyncSession):
    """
    Factory that creates and persists a User.

    Usage::

        user = await make_user()
        admin = await make_user(email="admin@example.com", username="admin")
    """

    async def _make_user(
        email: str | None = None,
        username: str | None = None,
        password: str = "Test1234!",
        is_active: bool = True,
        totp_enabled: bool = False,
        totp_secret: str | None = None,
        timezone: str = "UTC",
    ) -> User:
        uid = uuid.uuid4().hex[:8]
        user = User(
            email=email or f"user_{uid}@example.com",
            username=username or f"user_{uid}",
            hashed_pass=hash_password(password),
            is_active=is_active,
            totp_enabled=totp_enabled,
            totp_secret=totp_secret,
            timezone=timezone,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)
        return user

    return _make_user


@pytest_asyncio.fixture()
async def make_habit(db_session: AsyncSession):
    """
    Factory that creates and persists a Habit for a given user.

    Usage::

        habit = await make_habit(user=user)
        weekly = await make_habit(user=user, frequency="weekly")
    """

    async def _make_habit(
        user: User,
        name: str | None = None,
        description: str | None = None,
        frequency: str = "daily",
        target_days: list[int] | None = None,
        color: str = "#6366f1",
        icon: str = "check",
        notify_time=None,
        is_active: bool = True,
        sort_order: int = 0,
    ) -> Habit:
        uid = uuid.uuid4().hex[:6]
        habit = Habit(
            user_id=user.id,
            name=name or f"Habit {uid}",
            description=description,
            frequency=frequency,
            target_days=target_days or [1, 2, 3, 4, 5, 6, 7],
            color=color,
            icon=icon,
            notify_time=notify_time,
            is_active=is_active,
            sort_order=sort_order,
        )
        db_session.add(habit)
        await db_session.flush()
        await db_session.refresh(habit)
        return habit

    return _make_habit


@pytest_asyncio.fixture()
async def make_log(db_session: AsyncSession):
    """
    Factory that creates and persists a HabitLog.

    Usage::

        log = await make_log(habit=habit, user=user, log_date=date.today())
    """

    async def _make_log(
        habit: Habit,
        user: User,
        log_date: date | None = None,
        completed: bool = True,
        note: str | None = None,
    ) -> HabitLog:
        log = HabitLog(
            habit_id=habit.id,
            user_id=user.id,
            log_date=log_date or date.today(),
            completed=completed,
            note=note,
        )
        db_session.add(log)
        await db_session.flush()
        await db_session.refresh(log)
        return log

    return _make_log


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def get_auth_headers(user: User) -> dict[str, str]:
    """
    Returns Bearer auth headers for the given user.

    Usage::

        headers = get_auth_headers(user)
        response = await client.get("/api/v1/habits", headers=headers)
    """
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}
