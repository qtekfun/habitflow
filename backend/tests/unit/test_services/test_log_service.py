"""
Tests for log_service.py — written before implementation (TDD).

Covers:
- Check-in (create log)
- Duplicate check-in same day raises
- Undo check-in (delete log)
- Today's habits with completion status
- Stats: completion rate, weekly average
"""

from datetime import date

import pytest

from tests.conftest import days_ago


# ---------------------------------------------------------------------------
# Check-in
# ---------------------------------------------------------------------------


class TestCheckin:
    async def test_checkin_creates_log(self, db_session, make_user, make_habit):
        from app.services.log_service import checkin

        user = await make_user()
        habit = await make_habit(user=user)

        log = await checkin(db=db_session, habit=habit, user=user, log_date=date.today())

        assert log.id is not None
        assert log.habit_id == habit.id
        assert log.user_id == user.id
        assert log.log_date == date.today()
        assert log.completed is True

    async def test_checkin_with_note(self, db_session, make_user, make_habit):
        from app.services.log_service import checkin

        user = await make_user()
        habit = await make_habit(user=user)
        log = await checkin(
            db=db_session, habit=habit, user=user,
            log_date=date.today(), note="Felt great!"
        )

        assert log.note == "Felt great!"

    async def test_checkin_duplicate_same_day_raises(self, db_session, make_user, make_habit):
        from app.services.log_service import checkin, DuplicateLogError

        user = await make_user()
        habit = await make_habit(user=user)
        await checkin(db=db_session, habit=habit, user=user, log_date=date.today())

        with pytest.raises(DuplicateLogError):
            await checkin(db=db_session, habit=habit, user=user, log_date=date.today())

    async def test_checkin_different_days_ok(self, db_session, make_user, make_habit):
        from app.services.log_service import checkin

        user = await make_user()
        habit = await make_habit(user=user)
        log1 = await checkin(db=db_session, habit=habit, user=user, log_date=date.today())
        log2 = await checkin(db=db_session, habit=habit, user=user, log_date=days_ago(1))

        assert log1.id != log2.id


# ---------------------------------------------------------------------------
# Undo check-in
# ---------------------------------------------------------------------------


class TestUndoCheckin:
    async def test_undo_checkin_removes_log(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import undo_checkin, get_log

        user = await make_user()
        habit = await make_habit(user=user)
        log = await make_log(habit=habit, user=user, log_date=date.today())
        log_id = log.id

        await undo_checkin(db=db_session, log=log)

        result = await get_log(db=db_session, log_id=log_id, user_id=user.id)
        assert result is None

    async def test_get_log_wrong_user_returns_none(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import get_log

        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner)
        log = await make_log(habit=habit, user=owner, log_date=date.today())

        result = await get_log(db=db_session, log_id=log.id, user_id=other.id)
        assert result is None


# ---------------------------------------------------------------------------
# Today's habits with completion status
# ---------------------------------------------------------------------------


class TestTodayStatus:
    async def test_today_returns_all_active_habits(self, db_session, make_user, make_habit):
        from app.services.log_service import get_today_status

        user = await make_user()
        h1 = await make_habit(user=user, name="Run")
        h2 = await make_habit(user=user, name="Read")
        await make_habit(user=user, name="Inactive", is_active=False)

        results = await get_today_status(db=db_session, user_id=user.id, today=date.today())

        habit_ids = {r["habit_id"] for r in results}
        assert h1.id in habit_ids
        assert h2.id in habit_ids
        assert len(results) == 2

    async def test_today_marks_completed_habits(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import get_today_status

        user = await make_user()
        habit = await make_habit(user=user, name="Run")
        await make_log(habit=habit, user=user, log_date=date.today())

        results = await get_today_status(db=db_session, user_id=user.id, today=date.today())

        run_entry = next(r for r in results if r["habit_id"] == habit.id)
        assert run_entry["completed"] is True

    async def test_today_marks_incomplete_habits(self, db_session, make_user, make_habit):
        from app.services.log_service import get_today_status

        user = await make_user()
        habit = await make_habit(user=user, name="Read")

        results = await get_today_status(db=db_session, user_id=user.id, today=date.today())

        read_entry = next(r for r in results if r["habit_id"] == habit.id)
        assert read_entry["completed"] is False

    async def test_today_only_returns_user_habits(self, db_session, make_user, make_habit):
        from app.services.log_service import get_today_status

        user_a = await make_user()
        user_b = await make_user()
        habit_a = await make_habit(user=user_a, name="H1")
        await make_habit(user=user_b, name="H2")

        results_a = await get_today_status(db=db_session, user_id=user_a.id, today=date.today())
        results_b = await get_today_status(db=db_session, user_id=user_b.id, today=date.today())

        assert len(results_a) == 1
        assert results_a[0]["habit_id"] == habit_a.id
        assert len(results_b) == 1


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class TestStats:
    async def test_stats_completion_rate_100(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import get_stats

        user = await make_user()
        habit = await make_habit(user=user)
        for i in range(7):
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        stats = await get_stats(
            db=db_session, habit=habit,
            from_date=days_ago(6), to_date=date.today()
        )

        assert stats["total_days"] == 7
        assert stats["completed_days"] == 7
        assert stats["completion_rate"] == pytest.approx(1.0)

    async def test_stats_completion_rate_partial(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import get_stats

        user = await make_user()
        habit = await make_habit(user=user)
        for i in [0, 2, 4]:
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        stats = await get_stats(
            db=db_session, habit=habit,
            from_date=days_ago(6), to_date=date.today()
        )

        assert stats["completed_days"] == 3
        assert stats["completion_rate"] == pytest.approx(3 / 7)

    async def test_stats_completion_rate_zero(self, db_session, make_user, make_habit):
        from app.services.log_service import get_stats

        user = await make_user()
        habit = await make_habit(user=user)

        stats = await get_stats(
            db=db_session, habit=habit,
            from_date=days_ago(6), to_date=date.today()
        )

        assert stats["completed_days"] == 0
        assert stats["completion_rate"] == pytest.approx(0.0)

    async def test_stats_weekly_average(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import get_stats

        user = await make_user()
        habit = await make_habit(user=user)
        # 5 completions in week 1 (days 0-4), 3 in week 2 (days 7-9)
        for i in range(5):
            await make_log(habit=habit, user=user, log_date=days_ago(i))
        for i in range(7, 10):
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        stats = await get_stats(
            db=db_session, habit=habit,
            from_date=days_ago(13), to_date=date.today()
        )

        # 8 completions over 2 weeks = 4.0 average
        assert stats["weekly_average"] == pytest.approx(4.0)

    async def test_stats_respects_date_range(self, db_session, make_user, make_habit, make_log):
        from app.services.log_service import get_stats

        user = await make_user()
        habit = await make_habit(user=user)
        for i in range(10):
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        stats = await get_stats(
            db=db_session, habit=habit,
            from_date=days_ago(2), to_date=date.today()
        )

        assert stats["total_days"] == 3
        assert stats["completed_days"] == 3
