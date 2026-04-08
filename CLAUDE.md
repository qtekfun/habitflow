# HabitFlow — Agent Implementation Prompt

## Your mission

You are implementing **HabitFlow**, a self-hosted habit tracker.
The architecture, data model, API contract, and development methodology have already
been fully defined. Your job is to implement it following the decisions already made.
Do not redesign anything — follow the plan.

---

## Non-negotiable rules

1. **TDD strict**: write tests first, then implementation. Never the other way around.
2. **Coverage**: CI must enforce ≥ 80% on both backend and frontend. Do not lower this.
3. **English only**: all code, comments, commit messages, docstrings, variable names,
   file content, and README must be in English. No exceptions.
4. **Conventional commits**: `feat(auth): add TOTP setup endpoint`
5. **No secrets in repo**: `.env.example` documents all variables, `.env` is gitignored.
6. **Self-hosted first**: the default `compose.yml` includes its own PostgreSQL.
   Anyone with Docker installed must be able to run the project with zero external deps.
7. **Open source friendly**: clean structure, contribution guidelines, issue templates.

---

## Tech stack (already decided, do not change)

### Backend
- FastAPI 0.115+ (async)
- SQLAlchemy 2.x async + Alembic migrations
- PostgreSQL 16
- JWT access token (30 min) + refresh token httpOnly cookie (30 days) + temp token (5 min, TOTP flow)
- pyotp + qrcode for TOTP (RFC 6238)
- APScheduler 4.x for ntfy notifications (interval job every minute, timezone-aware)
- bcrypt via passlib
- Pydantic v2
- httpx for ntfy HTTP calls

### Frontend
- React 19 + TypeScript
- Vite 6
- Tailwind CSS v4 + shadcn/ui
- Zustand (auth store + habit store)
- TanStack Query v5
- React Hook Form + Zod
- Recharts (stats charts)
- vite-plugin-pwa + Workbox (PWA, installable on Android)
- react-i18next (EN + ES)

### Testing
- Backend: pytest + pytest-asyncio + httpx AsyncClient + pytest-cov (≥80%, blocks CI)
- Backend fuzz: Schemathesis against OpenAPI spec
- Frontend unit: Vitest + React Testing Library + v8 coverage (≥80%, blocks CI)
- Frontend E2E: Playwright (Chromium + Firefox)
- Mock HTTP in backend tests: pytest-httpx or respx

### DevOps
- GitHub Actions (CI backend, CI frontend, CD release on tag, weekly security scan)
- Dependabot for dependency updates
- Trivy for Docker image scanning
- pip-audit for Python deps
- Ruff (lint + format) + mypy (backend)
- ESLint + Prettier + tsc --noEmit (frontend)
- Multistage Dockerfiles (python:3.12-slim + node:22-alpine → nginx:alpine)
- Images published to ghcr.io on tag

---

## Repository structure

```
habitflow/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml
│   │   ├── ci-frontend.yml
│   │   ├── cd-release.yml
│   │   └── security-scan.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py        # pydantic-settings
│   │   │   ├── database.py      # async engine, session factory, get_db()
│   │   │   └── security.py      # JWT, bcrypt, TOTP helpers
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── habit.py
│   │   │   └── habit_log.py
│   │   ├── schemas/
│   │   │   ├── user.py          # UserCreate, UserRead, UserUpdate
│   │   │   ├── auth.py          # TokenResponse, LoginRequest, TOTPSetup
│   │   │   ├── habit.py         # HabitCreate, HabitRead, HabitUpdate
│   │   │   └── log.py           # LogCreate, LogRead, StatsResponse
│   │   ├── services/
│   │   │   ├── user_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── habit_service.py  # streak logic lives here
│   │   │   ├── log_service.py    # stats aggregation
│   │   │   └── ntfy_service.py   # httpx POST to ntfy
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── habits.py
│   │   │   └── logs.py
│   │   ├── scheduler.py          # APScheduler, runs inside backend container
│   │   └── main.py               # FastAPI app, lifespan, CORS middleware
│   ├── tests/
│   │   ├── conftest.py           # WRITE THIS FIRST
│   │   ├── unit/
│   │   │   ├── test_services/
│   │   │   │   ├── test_auth_service.py
│   │   │   │   ├── test_habit_service.py  # most complex: streak edge cases
│   │   │   │   ├── test_log_service.py
│   │   │   │   └── test_ntfy_service.py
│   │   │   └── test_routers/
│   │   │       ├── test_auth_router.py
│   │   │       ├── test_habits_router.py
│   │   │       └── test_logs_router.py
│   │   ├── integration/
│   │   │   └── test_full_flows.py
│   │   └── e2e/
│   │       └── test_api_contract.py  # Schemathesis
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── types/index.ts
│   │   ├── lib/
│   │   │   ├── api.ts            # axios instance + token refresh interceptor
│   │   │   └── utils.ts          # cn(), date helpers, streak formatters
│   │   ├── store/
│   │   │   ├── authStore.ts
│   │   │   └── habitStore.ts
│   │   ├── hooks/
│   │   │   ├── useHabits.ts
│   │   │   ├── useLogs.ts
│   │   │   └── useStats.ts
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui primitives
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   └── TOTPSetup.tsx
│   │   │   ├── habits/
│   │   │   │   ├── HabitCard.tsx
│   │   │   │   ├── HabitForm.tsx
│   │   │   │   ├── StreakBadge.tsx
│   │   │   │   └── HeatmapCalendar.tsx
│   │   │   └── layout/
│   │   │       ├── Navbar.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── HabitsPage.tsx
│   │   │   ├── StatsPage.tsx
│   │   │   ├── SettingsPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── components/
│   │   │   │   ├── HabitCard.test.tsx
│   │   │   │   ├── StreakBadge.test.tsx
│   │   │   │   └── TOTPSetup.test.tsx
│   │   │   ├── hooks/useHabits.test.ts
│   │   │   └── lib/utils.test.ts
│   │   └── e2e/
│   │       ├── auth.spec.ts
│   │       ├── habits.spec.ts
│   │       └── settings.spec.ts
│   ├── public/
│   │   ├── manifest.webmanifest
│   │   └── icons/
│   ├── index.html
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── deploy/
│   ├── compose.yml              # includes own PostgreSQL, zero external deps
│   ├── .env.example
│   └── traefik-labels.md        # optional: for users with existing Traefik
├── docs/
│   ├── deployment.md
│   ├── contributing.md
│   └── architecture.md
├── .gitignore
├── .editorconfig
├── README.md
└── CHANGELOG.md
```

---

## Data model

```sql
-- users
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         VARCHAR(255) UNIQUE NOT NULL
username      VARCHAR(50) UNIQUE NOT NULL
hashed_pass   TEXT NOT NULL
is_active     BOOLEAN DEFAULT TRUE
is_verified   BOOLEAN DEFAULT FALSE
totp_secret   TEXT                          -- NULL until 2FA enabled
totp_enabled  BOOLEAN DEFAULT FALSE
ntfy_url      TEXT                          -- e.g. https://ntfy.sh or self-hosted
ntfy_topic    TEXT                          -- user's private topic
ntfy_token    TEXT                          -- optional auth token
timezone      VARCHAR(50) DEFAULT 'UTC'
created_at    TIMESTAMPTZ DEFAULT NOW()
updated_at    TIMESTAMPTZ DEFAULT NOW()

-- habits
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id       UUID REFERENCES users(id) ON DELETE CASCADE
name          VARCHAR(100) NOT NULL
description   TEXT
color         VARCHAR(7) DEFAULT '#6366f1'
icon          VARCHAR(50) DEFAULT 'check'
frequency     VARCHAR(10) DEFAULT 'daily'   -- 'daily' | 'weekly'
target_days   INTEGER[] DEFAULT '{1,2,3,4,5,6,7}'  -- ISO weekdays (1=Mon)
notify_time   TIME                           -- NULL = no notification
is_active     BOOLEAN DEFAULT TRUE
sort_order    INTEGER DEFAULT 0
created_at    TIMESTAMPTZ DEFAULT NOW()
updated_at    TIMESTAMPTZ DEFAULT NOW()

-- habit_logs
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
habit_id      UUID REFERENCES habits(id) ON DELETE CASCADE
user_id       UUID REFERENCES users(id) ON DELETE CASCADE
log_date      DATE NOT NULL
completed     BOOLEAN DEFAULT TRUE
note          TEXT
created_at    TIMESTAMPTZ DEFAULT NOW()
UNIQUE(habit_id, log_date)
```

Computed fields (never stored, always calculated in habit_service.py):
- `current_streak`: consecutive completed days ending today or yesterday
- `longest_streak`: historical maximum
- `completion_rate`: completed / expected in date range
- `weekly_average`: completions per week over last N weeks

---

## API contract

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/login/totp
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/totp/setup
POST   /api/v1/auth/totp/verify
DELETE /api/v1/auth/totp

GET    /api/v1/users/me
PATCH  /api/v1/users/me
DELETE /api/v1/users/me
PATCH  /api/v1/users/me/password

GET    /api/v1/habits
POST   /api/v1/habits
GET    /api/v1/habits/{id}
PATCH  /api/v1/habits/{id}
DELETE /api/v1/habits/{id}
PATCH  /api/v1/habits/{id}/order

GET    /api/v1/logs
POST   /api/v1/logs
DELETE /api/v1/logs/{id}
GET    /api/v1/logs/today
GET    /api/v1/logs/stats

GET    /health
```

---

## Auth flow

```
# Without 2FA
POST /auth/login { email, password }
→ 200 { access_token, token_type: "bearer" }
  + Set-Cookie: refresh_token=<RT>; HttpOnly; SameSite=Strict

# With 2FA enabled
POST /auth/login { email, password }
→ 200 { totp_required: true, temp_token: <TT> }   # TT expires in 5 min, single use

POST /auth/login/totp { temp_token: <TT>, code: "482910" }
→ 200 { access_token }
  + Set-Cookie: refresh_token=...

# Token refresh
POST /auth/refresh   (cookie sent automatically)
→ 200 { access_token }
  + Set-Cookie: refresh_token=<new RT>   # old RT invalidated (rotation)

# TOTP setup
POST /auth/totp/setup
→ 200 { secret, qr_uri, backup_codes }

POST /auth/totp/verify { code: "482910" }
→ 200 { message: "2FA enabled" }
```

---

## Streak logic (most critical business logic — test every edge case)

```python
# Rules:
# - Streak counts consecutive completed days going backwards from today
# - If today is not yet completed, streak counts from yesterday (grace period)
# - Any missed day resets streak to 0
# - Weekly habits: streak counts consecutive weeks, not days
# - All date comparisons use the user's timezone, not UTC

# Edge cases to test explicitly:
# 1. Empty logs → streak = 0
# 2. Only today completed → streak = 1
# 3. Yesterday + today completed → streak = 2
# 4. Gap two days ago (today + yesterday ok, day before missing) → streak = 2
# 5. Only yesterday completed (today not yet) → streak = 1
# 6. Nothing completed in 2 days → streak = 0
# 7. User in UTC+9 checks at 23:00 UTC (next day in their timezone) → correct date
# 8. Weekly habit: completed this week + last week → streak = 2 weeks
# 9. Weekly habit: missed last week → streak = 1 (only this week)
```

---

## ntfy notification scheduler

```python
# Single APScheduler job, interval=1 minute
# Runs inside the backend container (not a separate service)
# Logic per tick:

async def dispatch_notifications():
    now_utc = datetime.now(timezone.utc)
    habits = await get_all_habits_with_notify_time()  # only where notify_time IS NOT NULL

    for habit in habits:
        user_tz = pytz.timezone(habit.user.timezone)
        now_local = now_utc.astimezone(user_tz)

        if (now_local.hour == habit.notify_time.hour and
                now_local.minute == habit.notify_time.minute):

            already_done = await is_completed_today(habit.id, now_local.date())
            if not already_done:
                await ntfy_service.send(
                    url=habit.user.ntfy_url,
                    topic=habit.user.ntfy_topic,
                    token=habit.user.ntfy_token,
                    habit_name=habit.name,
                    app_url="configured via env"
                )

# ntfy payload:
{
    "title": "HabitFlow",
    "message": f"Don't forget: {habit.name} 🎯",
    "tags": ["white_check_mark"],
    "priority": "default",
    "actions": [{"action": "view", "label": "Open app", "url": APP_URL}]
}
```

---

## Docker architecture

```yaml
# deploy/compose.yml — zero external dependencies
services:
  db:
    image: postgres:16-alpine
    volumes:
      - habitflow_pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    networks: [internal]
    healthcheck: pg_isready

  api:
    image: ghcr.io/[user]/habitflow-api:latest
    # or build: ../backend for local dev
    depends_on: [db]
    environment:
      DATABASE_URL, SECRET_KEY, ALLOWED_ORIGINS,
      ALLOW_REGISTRATION, APP_URL
    networks: [internal, traefik]
    labels: [traefik labels for habits-api.domain.com]

  web:
    image: ghcr.io/[user]/habitflow-web:latest
    # or build: ../frontend for local dev
    networks: [internal, traefik]
    labels: [traefik labels for habits.domain.com]

networks:
  internal: {}
  traefik:
    external: true   # optional — only needed if user has existing Traefik

volumes:
  habitflow_pgdata:
```

The `traefik` network should be **optional** — users without Traefik should be able
to expose ports directly. Document both options in `deploy/.env.example`.

---

## TDD implementation order — follow this exactly

```
PHASE 1 — Backend (tests first, then implementation)

Step 1: backend/tests/conftest.py
  - Async test database (separate from production DB)
  - AsyncClient fixture (httpx)
  - Factory fixtures: make_user(), make_habit(), make_log()
  - Auth helpers: get_auth_headers(user)

Step 2: tests/unit/test_services/test_auth_service.py → app/services/auth_service.py
  - test_register_creates_user
  - test_register_duplicate_email_raises
  - test_login_returns_tokens
  - test_login_wrong_password_raises
  - test_totp_setup_generates_secret
  - test_totp_verify_activates_2fa
  - test_totp_verify_wrong_code_raises
  - test_refresh_token_rotation
  - test_expired_refresh_token_raises

Step 3: tests/unit/test_services/test_habit_service.py → app/services/habit_service.py
  - test_create_habit
  - test_create_habit_wrong_user_raises
  - test_streak_empty_logs
  - test_streak_only_today
  - test_streak_yesterday_and_today
  - test_streak_broken_by_gap
  - test_streak_grace_period_today_not_done
  - test_streak_weekly_consecutive_weeks
  - test_streak_weekly_broken
  - test_streak_timezone_awareness
  - test_longest_streak

Step 4: tests/unit/test_services/test_log_service.py → app/services/log_service.py
  - test_checkin_creates_log
  - test_checkin_duplicate_same_day_raises
  - test_undo_checkin
  - test_today_returns_all_habits_with_status
  - test_stats_completion_rate
  - test_stats_weekly_average

Step 5: tests/unit/test_services/test_ntfy_service.py → app/services/ntfy_service.py
  - test_send_posts_correct_payload (mock httpx)
  - test_send_with_auth_token_adds_header
  - test_send_failure_does_not_raise (fire and forget)

Step 6: tests/unit/test_routers/ → app/routers/
  - HTTP-level tests for all endpoints
  - Test auth middleware (401 without token, 403 wrong user)
  - Test input validation (422 for bad payloads)

Step 7: tests/integration/test_full_flows.py
  - Full flow: register → login → setup 2FA → verify 2FA → create habit → check-in → verify streak

Step 8: tests/e2e/test_api_contract.py
  - Schemathesis fuzz against /openapi.json

PHASE 2 — Frontend (tests first, then implementation)

Step 1: tests/unit/lib/utils.test.ts → src/lib/utils.ts
  - formatStreak(), formatDate(), cn()

Step 2: tests/unit/hooks/useHabits.test.ts → src/hooks/useHabits.ts
  - MSW (Mock Service Worker) for API mocking

Step 3: Component tests → components
  - HabitCard, StreakBadge, TOTPSetup

Step 4: Playwright E2E
  - auth.spec.ts, habits.spec.ts, settings.spec.ts

PHASE 3 — DevOps
  - Dockerfiles
  - compose.yml
  - GitHub Actions workflows
  - README + docs
```

---

## GitHub Actions workflows

### ci-backend.yml
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_DB: habitflow_test, POSTGRES_USER: test, POSTGRES_PASSWORD: test }
        options: --health-cmd pg_isready
    steps:
      - checkout
      - setup Python 3.12
      - pip install -r requirements.txt -r requirements-dev.txt
      - ruff check .
      - ruff format --check .
      - mypy app/
      - pytest --cov=app --cov-fail-under=80 --cov-report=xml
      - upload coverage to Codecov
```

### ci-frontend.yml
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup Node 22
      - pnpm install
      - tsc --noEmit
      - eslint .
      - vitest run --coverage (fail under 80%)
      - playwright install --with-deps chromium firefox
      - playwright test
```

### cd-release.yml
```yaml
on:
  push:
    tags: ['v*']
jobs:
  release:
    - build backend image → ghcr.io/[user]/habitflow-api:[tag]
    - build frontend image → ghcr.io/[user]/habitflow-web:[tag]
    - create GitHub Release
```

### security-scan.yml
```yaml
on:
  schedule: ['0 8 * * 1']  # weekly Monday
  push:
    branches: [main]
jobs:
  scan:
    - trivy image habitflow-api
    - trivy image habitflow-web
    - pip-audit
    - upload SARIF to GitHub Security tab
```

---

## Environment variables (document all in deploy/.env.example)

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/habitflow
SECRET_KEY=                    # openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
ALLOWED_ORIGINS=https://habits.yourdomain.com
ALLOW_REGISTRATION=true        # set false after initial setup
APP_URL=https://habits.yourdomain.com
DEBUG=false

# Database (used by compose.yml)
POSTGRES_DB=habitflow
POSTGRES_USER=habitflow
POSTGRES_PASSWORD=             # generate strong password

# Frontend (build arg)
VITE_API_URL=https://habits-api.yourdomain.com
```

---

## README structure

```markdown
# HabitFlow

Self-hosted habit tracker. Track daily habits, build streaks,
get push notifications via ntfy. Installable as PWA.

## Features
- Daily and weekly habit tracking
- Streak calculation with statistics and heatmap
- TOTP 2FA (Ente Auth, Aegis, Google Authenticator compatible)
- Push notifications via ntfy (self-hosted or ntfy.sh)
- Installable PWA — no app store needed
- Multi-user
- Single Docker Compose deployment

## Quick start
[docker compose instructions]

## Configuration
[.env.example walkthrough]

## Development
[TDD workflow, how to run tests, coverage]

## Contributing
[conventional commits, PR process, branch strategy]
```

---

## What NOT to do

- Do not use synchronous SQLAlchemy (use async throughout)
- Do not store tokens in localStorage (use httpOnly cookies for refresh token)
- Do not skip tests to "speed up" — TDD is a hard requirement
- Do not lower coverage threshold below 80%
- Do not add external services to the default compose.yml (no Redis, no external auth)
- Do not write code before the test for that code exists
- Do not use Spanish in any code, comment, commit, or file
- Do not make the Traefik network required — it must be optional
# HabitFlow — Project Plan

Self-hosted habit tracker with streaks, statistics, push notifications via ntfy,
and PWA support. Open source, multi-user, deployable via Docker Compose.

---

## 1. Goals & Non-Goals

### Goals
- Track daily/weekly habits with streaks and statistics
- Multi-user with per-user ntfy notification settings
- TOTP-based 2FA (compatible with Ente Auth, Aegis, Google Authenticator)
- Installable PWA (no app store dependency)
- Self-hosted first: single compose.yml, no external dependencies
- Open source friendly: clean structure, contribution guidelines, CI enforced

### Non-Goals (v1)
- Native Android/iOS app (PWA covers this)
- Social/sharing features
- Habit templates marketplace
- AI-based suggestions

---

## 2. Tech Stack

### Backend
| Layer | Choice | Rationale |
|---|---|---|
| Framework | FastAPI 0.115+ | Async, OpenAPI auto-docs, trending in 2025-26 |
| ORM | SQLAlchemy 2.x (async) | Industry standard, Alembic migrations |
| Database | PostgreSQL 16 | Robust, already in homelab |
| Auth | JWT (access + refresh) + TOTP | Standard, stateless, 2FA without external deps |
| Scheduler | APScheduler 4.x | ntfy notifications per habit per user |
| Validation | Pydantic v2 | Co-located with FastAPI, fast |
| Password | bcrypt via passlib | Standard |
| TOTP | pyotp + qrcode | RFC 6238 compliant |

### Frontend
| Layer | Choice | Rationale |
|---|---|---|
| Framework | React 19 + TypeScript | Industry standard |
| Build | Vite 6 | Fastest DX, PWA plugin |
| Styling | Tailwind CSS v4 + shadcn/ui | Trending, composable |
| State | Zustand | Lightweight, minimal boilerplate |
| Data fetching | TanStack Query v5 | Cache, optimistic updates, loading states |
| Charts | Recharts | React-native, composable |
| Forms | React Hook Form + Zod | Type-safe, performant |
| PWA | vite-plugin-pwa + Workbox | Service worker, installable |
| i18n | react-i18next | EN + ES from day one |

### Testing
| Layer | Tool | Scope |
|---|---|---|
| Backend unit | pytest + pytest-asyncio | Services, models, utils |
| Backend integration | pytest + httpx AsyncClient | API endpoints end-to-end via test DB |
| Backend coverage | pytest-cov | Minimum 80%, blocks CI |
| Frontend unit | Vitest + React Testing Library | Components, hooks, stores |
| Frontend E2E | Playwright | Full user flows in browser |
| Frontend coverage | Vitest coverage (v8) | Minimum 80%, blocks CI |
| API contract | Schemathesis | Fuzz tests against OpenAPI schema |

### DevOps
| Concern | Tool |
|---|---|
| Containerization | Docker (multistage builds) |
| Orchestration | Docker Compose v2 |
| Reverse proxy | Traefik (user's existing setup) |
| CI/CD | GitHub Actions |
| Dependency updates | Dependabot |
| Linting | Ruff (backend), ESLint + Prettier (frontend) |
| Type checking | mypy (backend), tsc --noEmit (frontend) |
| Security scan | Trivy (Docker images), pip-audit |
| Secrets | Never in repo; .env.example with all keys documented |

---

## 3. Repository Structure

```
habitflow/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml        # lint, typecheck, test, coverage
│   │   ├── ci-frontend.yml       # lint, typecheck, test, coverage, playwright
│   │   ├── cd-release.yml        # build + push Docker images on tag
│   │   └── security-scan.yml     # Trivy + pip-audit weekly
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py         # Settings via pydantic-settings
│   │   │   ├── database.py       # Async engine, session factory
│   │   │   └── security.py       # JWT, bcrypt, TOTP helpers
│   │   ├── models/
│   │   │   ├── user.py           # User SQLAlchemy model
│   │   │   ├── habit.py          # Habit model
│   │   │   └── habit_log.py      # HabitLog model
│   │   ├── schemas/
│   │   │   ├── user.py           # UserCreate, UserRead, UserUpdate
│   │   │   ├── auth.py           # TokenResponse, LoginRequest, TOTPSetup
│   │   │   ├── habit.py          # HabitCreate, HabitRead, HabitUpdate
│   │   │   └── log.py            # LogCreate, LogRead, StatsResponse
│   │   ├── services/
│   │   │   ├── user_service.py   # User CRUD + password management
│   │   │   ├── auth_service.py   # Login, token refresh, TOTP verify
│   │   │   ├── habit_service.py  # Habit CRUD + streak calculation
│   │   │   ├── log_service.py    # Check-in, history, statistics
│   │   │   └── ntfy_service.py   # Push notification dispatch
│   │   ├── routers/
│   │   │   ├── auth.py           # /auth endpoints
│   │   │   ├── users.py          # /users endpoints
│   │   │   ├── habits.py         # /habits endpoints
│   │   │   └── logs.py           # /logs endpoints
│   │   ├── scheduler.py          # APScheduler: daily ntfy notifications
│   │   └── main.py               # FastAPI app, lifespan, middleware
│   │
│   ├── tests/
│   │   ├── conftest.py           # Fixtures: test DB, async client, users, habits
│   │   ├── unit/
│   │   │   ├── test_services/
│   │   │   │   ├── test_auth_service.py
│   │   │   │   ├── test_habit_service.py    # streak logic is complex: test thoroughly
│   │   │   │   ├── test_log_service.py      # stats aggregation
│   │   │   │   └── test_ntfy_service.py     # mock HTTP calls
│   │   │   └── test_routers/
│   │   │       ├── test_auth_router.py
│   │   │       ├── test_habits_router.py
│   │   │       └── test_logs_router.py
│   │   ├── integration/
│   │   │   └── test_full_flows.py  # register → 2FA → create habit → check-in → streak
│   │   └── e2e/
│   │       └── test_api_contract.py  # Schemathesis fuzz against OpenAPI
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/             # Migration files (auto-generated)
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── types/
│   │   │   └── index.ts          # Shared TypeScript interfaces
│   │   ├── lib/
│   │   │   ├── api.ts            # Axios instance + interceptors (token refresh)
│   │   │   └── utils.ts          # cn(), date helpers, streak formatters
│   │   ├── store/
│   │   │   ├── authStore.ts      # Zustand: user, tokens, 2FA state
│   │   │   └── habitStore.ts     # Zustand: habits cache
│   │   ├── hooks/
│   │   │   ├── useHabits.ts      # TanStack Query wrappers
│   │   │   ├── useLogs.ts
│   │   │   └── useStats.ts
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui primitives (Button, Card, Dialog…)
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   └── TOTPSetup.tsx  # QR code display + verify step
│   │   │   ├── habits/
│   │   │   │   ├── HabitCard.tsx        # Daily check-in card
│   │   │   │   ├── HabitForm.tsx        # Create/edit habit
│   │   │   │   ├── StreakBadge.tsx
│   │   │   │   └── HeatmapCalendar.tsx  # GitHub-style contribution graph
│   │   │   └── layout/
│   │   │       ├── Navbar.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx     # Today's habits + quick check-in
│   │   │   ├── HabitsPage.tsx    # Manage habits
│   │   │   ├── StatsPage.tsx     # Charts, heatmaps, streaks
│   │   │   ├── SettingsPage.tsx  # Profile, ntfy config, 2FA management
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── components/
│   │   │   │   ├── HabitCard.test.tsx
│   │   │   │   ├── StreakBadge.test.tsx
│   │   │   │   └── TOTPSetup.test.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useHabits.test.ts
│   │   │   └── lib/
│   │   │       └── utils.test.ts
│   │   └── e2e/
│   │       ├── auth.spec.ts       # Register, login, 2FA flow
│   │       ├── habits.spec.ts     # Create, check-in, streak
│   │       └── settings.spec.ts   # ntfy config, 2FA management
│   │
│   ├── public/
│   │   ├── manifest.webmanifest  # PWA manifest
│   │   └── icons/                # PWA icons (192, 512)
│   ├── index.html
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
│
├── deploy/
│   ├── compose.yml               # Production Docker Compose
│   ├── .env.example              # All required variables documented
│   └── traefik-labels.md         # Copy-paste labels for existing Traefik setups
│
├── docs/
│   ├── api.md                    # API reference (auto-generated from OpenAPI)
│   ├── deployment.md             # Step-by-step self-hosting guide
│   ├── contributing.md           # TDD workflow, commit conventions, PR process
│   └── architecture.md           # ADRs, decisions log
│
├── .gitignore
├── .editorconfig
├── README.md
└── CHANGELOG.md
```

---

## 4. Data Model

### users
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         VARCHAR(255) UNIQUE NOT NULL
username      VARCHAR(50) UNIQUE NOT NULL
hashed_pass   TEXT NOT NULL
is_active     BOOLEAN DEFAULT TRUE
is_verified   BOOLEAN DEFAULT FALSE
totp_secret   TEXT                        -- NULL until 2FA enabled
totp_enabled  BOOLEAN DEFAULT FALSE
ntfy_url      TEXT                        -- e.g. https://ntfy.sh or self-hosted
ntfy_topic    TEXT                        -- user's private topic
ntfy_token    TEXT                        -- optional auth token
timezone      VARCHAR(50) DEFAULT 'UTC'
created_at    TIMESTAMPTZ DEFAULT NOW()
updated_at    TIMESTAMPTZ DEFAULT NOW()
```

### habits
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id       UUID REFERENCES users(id) ON DELETE CASCADE
name          VARCHAR(100) NOT NULL
description   TEXT
color         VARCHAR(7) DEFAULT '#6366f1'  -- hex color for UI
icon          VARCHAR(50) DEFAULT 'check'   -- icon name
frequency     VARCHAR(10) DEFAULT 'daily'   -- daily | weekly
target_days   INTEGER[] DEFAULT '{1,2,3,4,5,6,7}'  -- weekdays for weekly habits
notify_time   TIME                           -- NULL = no notification
is_active     BOOLEAN DEFAULT TRUE
sort_order    INTEGER DEFAULT 0
created_at    TIMESTAMPTZ DEFAULT NOW()
updated_at    TIMESTAMPTZ DEFAULT NOW()
```

### habit_logs
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
habit_id      UUID REFERENCES habits(id) ON DELETE CASCADE
user_id       UUID REFERENCES users(id) ON DELETE CASCADE
log_date      DATE NOT NULL
completed     BOOLEAN DEFAULT TRUE
note          TEXT
created_at    TIMESTAMPTZ DEFAULT NOW()

UNIQUE(habit_id, log_date)
```

### Computed (no stored, always calculated)
- **current_streak**: consecutive completed days ending today or yesterday
- **longest_streak**: historical max
- **completion_rate**: logs completed / total expected in date range
- **weekly_average**: completions per week over last N weeks

---

## 5. API Contract

### Auth
```
POST /api/v1/auth/register          Create account (if ALLOW_REGISTRATION=true)
POST /api/v1/auth/login             Returns access + refresh tokens (or requires TOTP)
POST /api/v1/auth/login/totp        Submit TOTP code after password login
POST /api/v1/auth/refresh           Rotate refresh token
POST /api/v1/auth/logout            Invalidate refresh token
POST /api/v1/auth/totp/setup        Generate TOTP secret + QR code URI
POST /api/v1/auth/totp/verify       Verify code and activate 2FA
DELETE /api/v1/auth/totp            Disable 2FA (requires current TOTP code)
```

### Users
```
GET    /api/v1/users/me             Current user profile
PATCH  /api/v1/users/me             Update profile (username, timezone, ntfy settings)
DELETE /api/v1/users/me             Delete account + all data
PATCH  /api/v1/users/me/password    Change password
```

### Habits
```
GET    /api/v1/habits               List user's habits
POST   /api/v1/habits               Create habit
GET    /api/v1/habits/{id}          Get habit detail + current streak
PATCH  /api/v1/habits/{id}          Update habit
DELETE /api/v1/habits/{id}          Delete habit (soft delete)
PATCH  /api/v1/habits/{id}/order    Reorder habits
```

### Logs
```
GET    /api/v1/logs?habit_id=&from=&to=    Get log history
POST   /api/v1/logs                        Check-in (create log)
DELETE /api/v1/logs/{id}                   Undo check-in
GET    /api/v1/logs/today                  All habits with today's completion status
GET    /api/v1/logs/stats?habit_id=&range= Streak + completion stats
```

### Health
```
GET    /health                      { status, version }
```

---

## 6. Auth Flow (with TOTP)

```
1. POST /auth/register  →  account created, 2FA disabled
2. POST /auth/login     →  if totp_enabled=false → { access_token, refresh_token }
                           if totp_enabled=true  → { totp_required: true, temp_token }
3. POST /auth/login/totp (temp_token + code) → { access_token, refresh_token }
4. POST /auth/totp/setup  →  { secret, qr_uri, backup_codes }
5. POST /auth/totp/verify →  activates 2FA on account
```

Token strategy:
- **Access token**: 30 min, Bearer header
- **Refresh token**: 30 days, httpOnly cookie
- **Temp token** (post-password, pre-TOTP): 5 min, single use

---

## 7. Notification Flow

```
APScheduler (running inside backend container)
  └── Every minute: query habits WHERE notify_time = current_time (UTC, per user tz)
        └── For each habit: check if already completed today
              └── If NOT completed → POST to user's ntfy URL/topic
                    └── ntfy push arrives on user's phone
```

ntfy message format:
```
Title: "HabitFlow reminder"
Body:  "Don't forget: {habit.name} 🎯"
Tags:  ["white_check_mark"]
Priority: default
Actions: [{ action: "view", label: "Open app", url: "https://habits.domain.com" }]
```

---

## 8. PWA Strategy

- `manifest.webmanifest`: name, icons, theme_color, display=standalone, start_url=/
- Service Worker (Workbox via vite-plugin-pwa):
  - Cache-first for static assets
  - Network-first for API calls
  - Offline page for when API is unreachable
- Install prompt: custom "Add to Home Screen" banner
- iOS: `<meta>` apple-mobile-web-app tags for full-screen on Safari

---

## 9. Docker Architecture

```
deploy/compose.yml
  ├── habitflow-api      # FastAPI, port 8000 internal
  │     env: DATABASE_URL, SECRET_KEY, ALLOWED_ORIGINS, ALLOW_REGISTRATION
  ├── habitflow-web      # Nginx serving React build, port 80 internal
  │     env: VITE_API_URL (build arg)
  └── habitflow-db       # PostgreSQL 16, port 5432 internal
        volume: habitflow_pgdata

Networks:
  - traefik (external) → both api and web containers
  - habitflow_internal  → api ↔ db only

Traefik labels:
  habits.domain.com     → habitflow-web
  habits-api.domain.com → habitflow-api
```

Image strategy:
- **Backend Dockerfile**: python:3.12-slim base, multistage (builder + runtime)
- **Frontend Dockerfile**: node:22-alpine build → nginx:alpine serve
- Images published to `ghcr.io/[user]/habitflow-api` and `habitflow-web` on tag

---

## 10. CI/CD Pipeline

### ci-backend.yml (on PR + push to main)
```
1. Checkout
2. Setup Python 3.12
3. Install deps (requirements + requirements-dev)
4. ruff check + ruff format --check
5. mypy
6. pytest --cov=app --cov-fail-under=80 --cov-report=xml
7. Upload coverage to Codecov
```

### ci-frontend.yml (on PR + push to main)
```
1. Checkout
2. Setup Node 22
3. pnpm install
4. tsc --noEmit
5. eslint
6. vitest run --coverage (fail under 80%)
7. playwright install + playwright test
8. Upload coverage to Codecov
```

### cd-release.yml (on tag v*)
```
1. Build backend Docker image → ghcr.io
2. Build frontend Docker image → ghcr.io
3. Create GitHub Release with CHANGELOG extract
```

### security-scan.yml (weekly + on main push)
```
1. Trivy scan backend image
2. Trivy scan frontend image
3. pip-audit on requirements.txt
4. Upload SARIF to GitHub Security tab
```

---

## 11. TDD Development Order

Following strict TDD: **tests first, then implementation.**

### Phase 1 — Backend foundation
```
1. conftest.py                   # fixtures first: test DB, async client, factories
2. test_auth_service.py          # write tests
   → auth_service.py             # make tests pass
3. test_habit_service.py         # streak logic tests (edge cases: gaps, timezones)
   → habit_service.py
4. test_log_service.py           # stats tests
   → log_service.py
5. test_ntfy_service.py          # mock httpx tests
   → ntfy_service.py
6. test_auth_router.py           # HTTP-level tests
   → auth router
7. test_habits_router.py + test_logs_router.py
   → habits + logs routers
8. test_full_flows.py            # integration: full user journey
9. test_api_contract.py          # Schemathesis fuzz
```

### Phase 2 — Frontend
```
1. utils.test.ts                 # pure functions first
   → lib/utils.ts
2. useHabits.test.ts             # hook tests with MSW mocks
   → hooks/useHabits.ts
3. HabitCard.test.tsx            # component tests
   → HabitCard.tsx
4. StreakBadge.test.tsx → StreakBadge.tsx
5. TOTPSetup.test.tsx  → TOTPSetup.tsx
6. auth.spec.ts (Playwright)     # E2E: register → login → 2FA setup
7. habits.spec.ts (Playwright)   # E2E: create → check-in → streak visible
8. settings.spec.ts (Playwright) # E2E: ntfy config, disable 2FA
```

### Phase 3 — DevOps
```
1. Dockerfiles (backend + frontend)
2. compose.yml + .env.example
3. GitHub Actions workflows
4. README + deployment docs
```

---

## 12. Key Edge Cases to Test

### Streak logic (most complex business logic)
- Streak = 1 when only today is completed
- Streak continues if yesterday + today completed (not broken by "today not yet done")
- Streak breaks if any day is missed (not counting future days)
- Weekly habits: streak counts weeks, not days
- Timezone awareness: "today" is relative to user's timezone, not UTC
- Check-in after midnight in user's timezone still counts for "yesterday"

### Auth
- TOTP code reuse prevention (30s window, server-side used-code tracking)
- Expired temp_token after 5 min
- Refresh token rotation (old token invalidated on use)
- Rate limiting on login endpoint (prevent brute force)

### Multi-user isolation
- User A cannot see/modify User B's habits or logs
- All queries scoped by user_id (enforced at service layer, tested explicitly)

---

## 13. Commit Convention

Following Conventional Commits (same as homelab repo):
```
feat(auth): add TOTP setup endpoint
test(habits): add streak edge case for weekly frequency
fix(scheduler): correct timezone conversion for ntfy dispatch
docs(api): update auth flow diagram
chore(deps): bump fastapi to 0.115.5
```

Branch strategy:
- `main` — always deployable
- `feat/*` — feature branches, squash merge to main
- `fix/*` — bug fixes
- PRs require: CI green + coverage ≥ 80%

---

## 14. What This Project Demonstrates (Portfolio Value)

For Head of Engineering / VP Engineering roles, this project shows:

- **Architecture decisions**: async Python, TDD discipline, clean layering
- **Security mindset**: 2FA, JWT rotation, rate limiting, Trivy scans, no secrets in repo
- **DevOps maturity**: multistage Docker, GitHub Actions, Dependabot, SARIF
- **Open source ownership**: contribution guidelines, issue templates, CHANGELOG
- **Product thinking**: PWA over native, ntfy over Firebase (privacy-first)
- **Self-hosting philosophy**: zero external dependencies, works air-gapped
