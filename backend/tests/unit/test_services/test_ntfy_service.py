"""
Tests for ntfy_service.py — written before implementation (TDD).

Covers:
- Correct payload structure sent to ntfy
- Auth token header added when provided
- Missing ntfy config (no url/topic) silently skips
- HTTP errors do not propagate (fire-and-forget)
- Network errors do not propagate (fire-and-forget)
"""

from pytest_httpx import HTTPXMock


NTFY_URL = "https://ntfy.sh"
NTFY_TOPIC = "habitflow-test-topic"
HABIT_NAME = "Meditate"
APP_URL = "https://habits.example.com"


# ---------------------------------------------------------------------------
# Correct payload
# ---------------------------------------------------------------------------


class TestNtfySend:
    async def test_send_posts_to_correct_url(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send

        httpx_mock.add_response(url=f"{NTFY_URL}/{NTFY_TOPIC}", status_code=200)

        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert requests[0].method == "POST"

    async def test_send_payload_contains_habit_name(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send

        httpx_mock.add_response(url=f"{NTFY_URL}/{NTFY_TOPIC}", status_code=200)

        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

        import json

        body = json.loads(httpx_mock.get_requests()[0].content)
        assert HABIT_NAME in body["message"]
        assert body["title"] == "HabitFlow"
        assert "white_check_mark" in body["tags"]

    async def test_send_payload_contains_app_url_action(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send

        httpx_mock.add_response(url=f"{NTFY_URL}/{NTFY_TOPIC}", status_code=200)

        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

        import json

        body = json.loads(httpx_mock.get_requests()[0].content)
        actions = body.get("actions", [])
        assert any(a.get("url") == APP_URL for a in actions)

    async def test_send_with_token_adds_auth_header(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send

        httpx_mock.add_response(url=f"{NTFY_URL}/{NTFY_TOPIC}", status_code=200)

        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token="secret-token",
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

        request = httpx_mock.get_requests()[0]
        assert request.headers.get("Authorization") == "Bearer secret-token"

    async def test_send_without_token_has_no_auth_header(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send

        httpx_mock.add_response(url=f"{NTFY_URL}/{NTFY_TOPIC}", status_code=200)

        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

        request = httpx_mock.get_requests()[0]
        assert "Authorization" not in request.headers


# ---------------------------------------------------------------------------
# Fire-and-forget — errors must not propagate
# ---------------------------------------------------------------------------


class TestNtfyFireAndForget:
    async def test_http_error_does_not_raise(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send

        httpx_mock.add_response(url=f"{NTFY_URL}/{NTFY_TOPIC}", status_code=500)

        # Must not raise
        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

    async def test_network_error_does_not_raise(self, httpx_mock: HTTPXMock):
        from app.services.ntfy_service import send
        import httpx

        httpx_mock.add_exception(
            httpx.ConnectError("Connection refused"),
            url=f"{NTFY_URL}/{NTFY_TOPIC}",
        )

        # Must not raise
        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )


# ---------------------------------------------------------------------------
# Missing config — silently skip
# ---------------------------------------------------------------------------


class TestNtfyMissingConfig:
    async def test_no_url_skips_silently(self):
        from app.services.ntfy_service import send

        # No httpx_mock — if an HTTP call were made it would raise
        await send(
            ntfy_url=None,
            ntfy_topic=NTFY_TOPIC,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )

    async def test_no_topic_skips_silently(self):
        from app.services.ntfy_service import send

        await send(
            ntfy_url=NTFY_URL,
            ntfy_topic=None,
            ntfy_token=None,
            habit_name=HABIT_NAME,
            app_url=APP_URL,
        )
