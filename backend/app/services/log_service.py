"""
log_service.py — check-in, undo, today status, and stats aggregation.
"""

from __future__ import annotations

import math
import uuid
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.user import User


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------


class DuplicateLogError(Exception):
    """Raised when a check-in already exists for the given habit + date."""


# ---------------------------------------------------------------------------
# Check-in
# ---------------------------------------------------------------------------


async def checkin(
    *,
    db: AsyncSession,
    habit: Habit,
    user: User,
    log_date: date,
    note: str | None = None,
) -> HabitLog:
    """Create a completed log for *habit* on *log_date*.

    Raises DuplicateLogError if a log already exists for that date.
    """
    existing = await db.execute(
        select(HabitLog).where(
            and_(HabitLog.habit_id == habit.id, HabitLog.log_date == log_date)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateLogError(f"Habit {habit.id} already checked in on {log_date}")

    log = HabitLog(
        habit_id=habit.id,
        user_id=user.id,
        log_date=log_date,
        completed=True,
        note=note,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


# ---------------------------------------------------------------------------
# Undo check-in
# ---------------------------------------------------------------------------


async def undo_checkin(*, db: AsyncSession, log: HabitLog) -> None:
    """Delete *log*, effectively undoing the check-in."""
    await db.delete(log)
    await db.flush()


async def get_log(
    *, db: AsyncSession, log_id: uuid.UUID, user_id: uuid.UUID
) -> HabitLog | None:
    """Return a log only when it belongs to *user_id*."""
    result = await db.execute(
        select(HabitLog).where(and_(HabitLog.id == log_id, HabitLog.user_id == user_id))
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Today's habit status
# ---------------------------------------------------------------------------


async def get_today_status(
    *, db: AsyncSession, user_id: uuid.UUID, today: date
) -> list[dict]:
    """Return all active habits for *user_id* with today's completion flag.

    Each entry: {"habit_id": UUID, "name": str, "completed": bool, "log_id": UUID | None}
    """
    habits_result = await db.execute(
        select(Habit).where(and_(Habit.user_id == user_id, Habit.is_active.is_(True)))
    )
    habits = habits_result.scalars().all()

    if not habits:
        return []

    habit_ids = [h.id for h in habits]
    logs_result = await db.execute(
        select(HabitLog).where(
            and_(
                HabitLog.habit_id.in_(habit_ids),
                HabitLog.log_date == today,
                HabitLog.completed.is_(True),
            )
        )
    )
    completed_today: dict[uuid.UUID, uuid.UUID] = {
        log.habit_id: log.id for log in logs_result.scalars().all()
    }

    return [
        {
            "habit_id": h.id,
            "name": h.name,
            "completed": h.id in completed_today,
            "log_id": completed_today.get(h.id),
        }
        for h in habits
    ]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def get_stats(
    *,
    db: AsyncSession,
    habit: Habit,
    from_date: date,
    to_date: date,
) -> dict:
    """Compute completion stats for *habit* over [from_date, to_date] (inclusive).

    Returns:
        total_days       — number of calendar days in the range
        completed_days   — days with a completed log in the range
        completion_rate  — completed_days / total_days  (0.0 if total_days == 0)
        weekly_average   — completed_days / number_of_weeks  (ceil-rounded weeks)
    """
    total_days = (to_date - from_date).days + 1

    result = await db.execute(
        select(HabitLog).where(
            and_(
                HabitLog.habit_id == habit.id,
                HabitLog.completed.is_(True),
                HabitLog.log_date >= from_date,
                HabitLog.log_date <= to_date,
            )
        )
    )
    completed_days = len(result.scalars().all())

    completion_rate = completed_days / total_days if total_days > 0 else 0.0

    # Number of (partial) weeks in the range — ceiling division.
    num_weeks = math.ceil(total_days / 7)
    weekly_average = completed_days / num_weeks if num_weeks > 0 else 0.0

    return {
        "total_days": total_days,
        "completed_days": completed_days,
        "completion_rate": completion_rate,
        "weekly_average": weekly_average,
    }
