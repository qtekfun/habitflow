"""
Habit service.

Responsibilities:
- Habit CRUD (scoped to user_id)
- Streak calculation for daily and weekly habits
- Longest streak calculation
- All date comparisons are timezone-aware (user's local date)
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.habit_log import HabitLog


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def create_habit(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    description: str | None = None,
    frequency: str = "daily",
    target_days: list[int] | None = None,
    color: str = "#6366f1",
    icon: str = "check",
    notify_time=None,
    sort_order: int = 0,
) -> Habit:
    habit = Habit(
        user_id=user_id,
        name=name,
        description=description,
        frequency=frequency,
        target_days=target_days or [1, 2, 3, 4, 5, 6, 7],
        color=color,
        icon=icon,
        notify_time=notify_time,
        sort_order=sort_order,
    )
    db.add(habit)
    await db.flush()
    await db.refresh(habit)
    return habit


async def get_habit(
    *,
    db: AsyncSession,
    habit_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Habit | None:
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_habits(
    *,
    db: AsyncSession,
    user_id: uuid.UUID,
    active_only: bool = True,
) -> list[Habit]:
    query = select(Habit).where(Habit.user_id == user_id)
    if active_only:
        query = query.where(Habit.is_active.is_(True))
    query = query.order_by(Habit.sort_order, Habit.created_at)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_habit(*, db: AsyncSession, habit: Habit, **kwargs) -> Habit:
    for key, value in kwargs.items():
        if hasattr(habit, key) and value is not None:
            setattr(habit, key, value)
    db.add(habit)
    await db.flush()
    await db.refresh(habit)
    return habit


async def delete_habit(*, db: AsyncSession, habit: Habit) -> None:
    await db.delete(habit)
    await db.flush()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _today_in_tz(user_timezone: str) -> date:
    tz = pytz.timezone(user_timezone)
    return datetime.now(timezone.utc).astimezone(tz).date()


def _current_iso_week(user_timezone: str) -> tuple[int, int]:
    """Return (year, week_number) for the current week in user's timezone."""
    today = _today_in_tz(user_timezone)
    iso = today.isocalendar()
    return iso.year, iso.week


def _iso_week_of(d: date) -> tuple[int, int]:
    iso = d.isocalendar()
    return iso.year, iso.week


async def _completed_dates(db: AsyncSession, habit: Habit) -> set[date]:
    """Return the set of all dates where this habit was completed."""
    result = await db.execute(
        select(HabitLog.log_date).where(
            HabitLog.habit_id == habit.id,
            HabitLog.completed.is_(True),
        )
    )
    return {row[0] for row in result.all()}


# ---------------------------------------------------------------------------
# Streak — daily habits
# ---------------------------------------------------------------------------


def _daily_streak(completed: set[date], today: date) -> int:
    """
    Count consecutive completed days ending today or yesterday (grace period).

    Rules:
    - Start from today; if today not completed, start from yesterday.
    - Walk backwards day by day; stop at first missing day.
    """
    if not completed:
        return 0

    # Determine the starting point (grace period: skip today if not done)
    if today in completed:
        cursor = today
    elif (today - timedelta(days=1)) in completed:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in completed:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


# ---------------------------------------------------------------------------
# Streak — weekly habits
# ---------------------------------------------------------------------------


def _weekly_streak(completed: set[date], today: date) -> int:
    """
    Count consecutive completed weeks ending this week or last week (grace).

    A week is considered "completed" if at least one log falls in it.
    Grace period: if this week has no log yet, check starting from last week.
    """
    if not completed:
        return 0

    completed_weeks: set[tuple[int, int]] = {_iso_week_of(d) for d in completed}

    this_week = _iso_week_of(today)
    last_week = _iso_week_of(today - timedelta(weeks=1))

    if this_week in completed_weeks:
        current = this_week
    elif last_week in completed_weeks:
        current = last_week
    else:
        return 0

    streak = 0
    check_date = today if current == this_week else today - timedelta(weeks=1)

    while _iso_week_of(check_date) in completed_weeks:
        streak += 1
        check_date -= timedelta(weeks=1)

    return streak


# ---------------------------------------------------------------------------
# Public streak API
# ---------------------------------------------------------------------------


async def calculate_streak(
    *,
    db: AsyncSession,
    habit: Habit,
    user_timezone: str = "UTC",
) -> int:
    completed = await _completed_dates(db, habit)
    today = _today_in_tz(user_timezone)

    if habit.frequency == "weekly":
        return _weekly_streak(completed, today)
    return _daily_streak(completed, today)


async def calculate_longest_streak(
    *,
    db: AsyncSession,
    habit: Habit,
) -> int:
    """
    Calculate the historical longest consecutive streak (daily only).
    Scans all logs in chronological order.
    """
    completed = await _completed_dates(db, habit)
    if not completed:
        return 0

    sorted_dates = sorted(completed)
    longest = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return longest
