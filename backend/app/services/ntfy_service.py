"""
ntfy_service.py — fire-and-forget push notifications via ntfy.

Sends a POST to <ntfy_url>/<ntfy_topic> with a structured JSON payload.
All errors are swallowed; notification delivery is best-effort.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def send(
    *,
    ntfy_url: str | None,
    ntfy_topic: str | None,
    ntfy_token: str | None,
    habit_name: str,
    app_url: str,
) -> None:
    """Post a reminder notification to the user's ntfy endpoint.

    Silently skips if ntfy_url or ntfy_topic is not configured.
    Never raises — delivery is fire-and-forget.
    """
    if not ntfy_url or not ntfy_topic:
        return

    payload = {
        "title": "HabitFlow",
        "message": f"Don't forget: {habit_name} 🎯",
        "tags": ["white_check_mark"],
        "priority": "default",
        "actions": [{"action": "view", "label": "Open app", "url": app_url}],
    }

    headers: dict[str, str] = {}
    if ntfy_token:
        headers["Authorization"] = f"Bearer {ntfy_token}"

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{ntfy_url}/{ntfy_topic}",
                json=payload,
                headers=headers,
            )
    except Exception:
        logger.warning(
            "ntfy notification failed for habit %r", habit_name, exc_info=True
        )
