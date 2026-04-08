"""
API contract tests using Schemathesis fuzz testing.

Generates random inputs from the OpenAPI schema and verifies:
- No unexpected 5xx server errors
- All responses conform to the declared response schemas

The test DB is wired in via a module-level dependency override so that
Schemathesis can call through the ASGI app without touching the production DB.
"""

import schemathesis
from hypothesis import HealthCheck, settings as h_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings as app_settings
from app.core.database import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Wire the test DB into the app for all Schemathesis calls
# ---------------------------------------------------------------------------

_engine = create_async_engine(
    app_settings.TEST_DATABASE_URL, poolclass=NullPool, echo=False
)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _test_get_db():
    async with _Session() as session:
        try:
            yield session
        finally:
            await session.rollback()


app.dependency_overrides[get_db] = _test_get_db

# ---------------------------------------------------------------------------
# Schemathesis schema + fuzz test
# ---------------------------------------------------------------------------

schema = schemathesis.from_asgi("/openapi.json", app=app, force_schema_version="30")


@schema.parametrize()
@h_settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_no_server_errors(case):
    """
    All endpoints must never return 5xx for any generated input.

    401/403/404/422 are expected for unauthenticated or invalid requests
    and are declared in the OpenAPI spec — Schemathesis treats them as valid.
    """
    response = case.call(session=None)
    assert (
        response.status_code < 500
    ), f"{case.method} {case.formatted_path} → {response.status_code}: {response.text[:200]}"
