"""
Tests for habit_service.py — written before implementation (TDD).

Covers:
- Habit CRUD
- Streak calculation (all edge cases from the spec)
- Longest streak
- Timezone-aware date handling
"""

from datetime import date, timedelta

import pytz

from tests.conftest import days_ago


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestHabitCRUD:
    async def test_create_habit(self, db_session, make_user):
        from app.services.habit_service import create_habit

        user = await make_user()
        habit = await create_habit(
            db=db_session,
            user_id=user.id,
            name="Meditate",
            description="10 minutes",
            frequency="daily",
            color="#6366f1",
            icon="brain",
        )

        assert habit.id is not None
        assert habit.name == "Meditate"
        assert habit.user_id == user.id
        assert habit.frequency == "daily"
        assert habit.is_active is True

    async def test_create_habit_sets_default_target_days(self, db_session, make_user):
        from app.services.habit_service import create_habit

        user = await make_user()
        habit = await create_habit(db=db_session, user_id=user.id, name="Run")

        assert habit.target_days == [1, 2, 3, 4, 5, 6, 7]

    async def test_get_habit_by_id(self, db_session, make_user, make_habit):
        from app.services.habit_service import get_habit

        user = await make_user()
        habit = await make_habit(user=user, name="Yoga")

        fetched = await get_habit(db=db_session, habit_id=habit.id, user_id=user.id)
        assert fetched is not None
        assert fetched.id == habit.id

    async def test_get_habit_wrong_user_returns_none(
        self, db_session, make_user, make_habit
    ):
        from app.services.habit_service import get_habit

        owner = await make_user()
        other = await make_user()
        habit = await make_habit(user=owner, name="Yoga")

        result = await get_habit(db=db_session, habit_id=habit.id, user_id=other.id)
        assert result is None

    async def test_list_habits_returns_only_user_habits(
        self, db_session, make_user, make_habit
    ):
        from app.services.habit_service import list_habits

        user_a = await make_user()
        user_b = await make_user()
        await make_habit(user=user_a, name="H1")
        await make_habit(user=user_a, name="H2")
        await make_habit(user=user_b, name="H3")

        habits = await list_habits(db=db_session, user_id=user_a.id)
        assert len(habits) == 2
        assert all(h.user_id == user_a.id for h in habits)

    async def test_update_habit(self, db_session, make_user, make_habit):
        from app.services.habit_service import update_habit

        user = await make_user()
        habit = await make_habit(user=user, name="Old name")

        updated = await update_habit(
            db=db_session,
            habit=habit,
            name="New name",
            color="#ff0000",
        )

        assert updated.name == "New name"
        assert updated.color == "#ff0000"

    async def test_delete_habit(self, db_session, make_user, make_habit):
        from app.services.habit_service import delete_habit, get_habit

        user = await make_user()
        habit = await make_habit(user=user)
        habit_id = habit.id

        await delete_habit(db=db_session, habit=habit)

        result = await get_habit(db=db_session, habit_id=habit_id, user_id=user.id)
        assert result is None


# ---------------------------------------------------------------------------
# Streak calculation — daily habits
# ---------------------------------------------------------------------------


class TestDailyStreak:
    async def test_streak_empty_logs(self, db_session, make_user, make_habit):
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 0

    async def test_streak_only_today(self, db_session, make_user, make_habit, make_log):
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=date.today())

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 1

    async def test_streak_yesterday_and_today(
        self, db_session, make_user, make_habit, make_log
    ):
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=date.today())
        await make_log(habit=habit, user=user, log_date=days_ago(1))

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 2

    async def test_streak_broken_by_gap(
        self, db_session, make_user, make_habit, make_log
    ):
        """today + yesterday OK, day before yesterday missing → streak = 2."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=date.today())
        await make_log(habit=habit, user=user, log_date=days_ago(1))
        # days_ago(2) is missing — gap
        await make_log(habit=habit, user=user, log_date=days_ago(3))

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 2

    async def test_streak_grace_period_today_not_done(
        self, db_session, make_user, make_habit, make_log
    ):
        """Only yesterday completed; today not yet done → streak = 1 (grace period)."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=days_ago(1))

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 1

    async def test_streak_nothing_in_two_days(
        self, db_session, make_user, make_habit, make_log
    ):
        """No completion for 2 days → streak = 0."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=days_ago(2))
        await make_log(habit=habit, user=user, log_date=days_ago(3))

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 0

    async def test_streak_only_older_logs(
        self, db_session, make_user, make_habit, make_log
    ):
        """Logs exist but none within grace window → streak = 0."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        for i in range(5, 10):
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 0

    async def test_streak_long_consecutive_run(
        self, db_session, make_user, make_habit, make_log
    ):
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user)
        for i in range(30):  # 30 consecutive days ending today
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 30


# ---------------------------------------------------------------------------
# Streak — timezone awareness
# ---------------------------------------------------------------------------


class TestStreakTimezone:
    async def test_streak_timezone_utc_plus9(
        self, db_session, make_user, make_habit, make_log
    ):
        """
        A user in UTC+9 whose local date is 'tomorrow' relative to UTC should
        still see today's log counted correctly.
        """
        from app.services.habit_service import calculate_streak

        # Simulate: it is 23:00 UTC, but the user is UTC+9 → 08:00 next day locally.
        # "Today" for the user is the UTC date + 1.
        tz = pytz.timezone("Asia/Tokyo")  # UTC+9

        # Compute what "today" is in Tokyo right now — we'll log that date.
        import datetime as dt

        now_utc = dt.datetime.now(dt.timezone.utc)
        today_in_tz = now_utc.astimezone(tz).date()

        user = await make_user(timezone="Asia/Tokyo")
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=today_in_tz)
        yesterday_in_tz = today_in_tz - timedelta(days=1)
        await make_log(habit=habit, user=user, log_date=yesterday_in_tz)

        streak = await calculate_streak(
            db=db_session, habit=habit, user_timezone="Asia/Tokyo"
        )
        assert streak == 2

    async def test_streak_uses_user_timezone_not_utc(
        self, db_session, make_user, make_habit, make_log
    ):
        """
        A log for 'today in UTC-8' may be 'yesterday in UTC'. Streak must be 1,
        not 0, when the log date matches the user's local today.
        """
        from app.services.habit_service import calculate_streak
        import datetime as dt

        tz = pytz.timezone("America/Los_Angeles")  # UTC-8 (standard)
        now_utc = dt.datetime.now(dt.timezone.utc)
        today_in_tz = now_utc.astimezone(tz).date()

        user = await make_user(timezone="America/Los_Angeles")
        habit = await make_habit(user=user)
        await make_log(habit=habit, user=user, log_date=today_in_tz)

        streak = await calculate_streak(
            db=db_session, habit=habit, user_timezone="America/Los_Angeles"
        )
        assert streak == 1


# ---------------------------------------------------------------------------
# Streak — weekly habits
# ---------------------------------------------------------------------------


class TestWeeklyStreak:
    @staticmethod
    def _iso_week_monday(weeks_ago: int) -> date:
        iso = date.today().isocalendar()
        this_monday = date.fromisocalendar(iso.year, iso.week, 1)
        return this_monday - timedelta(weeks=weeks_ago)

    async def test_streak_weekly_consecutive_weeks(
        self, db_session, make_user, make_habit, make_log
    ):
        """Completed this week + last week → streak = 2."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user, frequency="weekly")
        this_week = self._iso_week_monday(0)
        last_week = self._iso_week_monday(1)
        await make_log(habit=habit, user=user, log_date=this_week)
        await make_log(habit=habit, user=user, log_date=last_week)

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 2

    async def test_streak_weekly_broken(
        self, db_session, make_user, make_habit, make_log
    ):
        """Missed last week → streak = 1 (only this week counts)."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user, frequency="weekly")
        this_week = self._iso_week_monday(0)
        two_weeks_ago = self._iso_week_monday(2)
        await make_log(habit=habit, user=user, log_date=this_week)
        await make_log(habit=habit, user=user, log_date=two_weeks_ago)

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 1

    async def test_streak_weekly_grace_this_week_not_done(
        self, db_session, make_user, make_habit, make_log
    ):
        """This week not done yet, last week done → streak = 1 (weekly grace period)."""
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user, frequency="weekly")
        last_week = self._iso_week_monday(1)
        two_weeks_ago = self._iso_week_monday(2)
        await make_log(habit=habit, user=user, log_date=last_week)
        await make_log(habit=habit, user=user, log_date=two_weeks_ago)

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 2

    async def test_streak_weekly_empty(self, db_session, make_user, make_habit):
        from app.services.habit_service import calculate_streak

        user = await make_user()
        habit = await make_habit(user=user, frequency="weekly")

        streak = await calculate_streak(db=db_session, habit=habit, user_timezone="UTC")
        assert streak == 0


# ---------------------------------------------------------------------------
# Longest streak
# ---------------------------------------------------------------------------


class TestLongestStreak:
    async def test_longest_streak_basic(
        self, db_session, make_user, make_habit, make_log
    ):
        from app.services.habit_service import calculate_longest_streak

        user = await make_user()
        habit = await make_habit(user=user)
        # 5-day run, then a gap, then 2-day run
        for i in range(10, 5, -1):  # days 10..6 ago (5 days)
            await make_log(habit=habit, user=user, log_date=days_ago(i))
        # gap at day 5
        for i in range(4, 2, -1):  # days 4..3 ago (2 days)
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        longest = await calculate_longest_streak(db=db_session, habit=habit)
        assert longest == 5

    async def test_longest_streak_empty(self, db_session, make_user, make_habit):
        from app.services.habit_service import calculate_longest_streak

        user = await make_user()
        habit = await make_habit(user=user)

        longest = await calculate_longest_streak(db=db_session, habit=habit)
        assert longest == 0

    async def test_longest_streak_all_consecutive(
        self, db_session, make_user, make_habit, make_log
    ):
        from app.services.habit_service import calculate_longest_streak

        user = await make_user()
        habit = await make_habit(user=user)
        for i in range(20):
            await make_log(habit=habit, user=user, log_date=days_ago(i))

        longest = await calculate_longest_streak(db=db_session, habit=habit)
        assert longest == 20
