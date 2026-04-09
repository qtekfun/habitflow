# HabitFlow — Session Handoff

## Where we are

**Phase 1 backend: COMPLETE.**
**Phase 2 frontend: NOT STARTED — this is the next step.**

---

## Completed work (all committed & pushed to master)

| Step | What | Tests | Coverage |
|------|------|-------|----------|
| 1 | `tests/conftest.py` — async test DB, factories, fixtures | — | — |
| 2 | `test_auth_service.py` → `auth_service.py` | 20 | — |
| 3 | `test_habit_service.py` → `habit_service.py` | 24 | — |
| 4 | `test_log_service.py` → `log_service.py` | 15 | — |
| 5 | `test_ntfy_service.py` → `ntfy_service.py` | 9 | — |
| 6 | `test_*_router.py` → routers + schemas + deps | 47 | — |
| 7 | `test_full_flows.py` (integration) | 9 | — |
| 8 | `test_api_contract.py` (Schemathesis fuzz, 18 endpoints) | 18 | — |
| **Total** | | **142** | **90.8%** |

All CI checks pass: ruff, mypy, pytest-cov ≥ 80%.

---

## What exists in the repo

```
backend/
├── app/
│   ├── core/        config.py, database.py, security.py
│   ├── models/      user.py, habit.py, habit_log.py
│   ├── schemas/     auth.py, user.py, habit.py, log.py
│   ├── services/    auth_service.py, habit_service.py, log_service.py, ntfy_service.py
│   ├── routers/     auth.py, habits.py, logs.py
│   ├── dependencies.py
│   ├── main.py
│   └── scheduler.py  (stub — APScheduler wired in later)
├── tests/
│   ├── conftest.py
│   ├── unit/test_services/ + unit/test_routers/
│   ├── integration/test_full_flows.py
│   └── e2e/test_api_contract.py
├── alembic/          (stub)
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
.github/workflows/   ci-backend.yml, ci-frontend.yml, cd-release.yml, security-scan.yml
```

Frontend directory does NOT exist yet.

---

## Next session: Phase 2 — Frontend

### Pre-requisites on the new machine

1. **Node.js 22** + **pnpm** must be installed.
   - Install Node: https://nodejs.org (LTS) or via nvm
   - Install pnpm: `npm install -g pnpm`
2. Docker running with the test DB container (port 5433) — only needed if running backend tests.

### Phase 2 TDD order (follow exactly, tests before implementation)

```
Step 1 — utils
  tests/unit/lib/utils.test.ts   ← write first
  src/lib/utils.ts               ← then implement

Step 2 — useHabits hook
  tests/unit/hooks/useHabits.test.ts  ← write first (MSW for API mocking)
  src/hooks/useHabits.ts              ← then implement

Step 3 — Components
  tests/unit/components/HabitCard.test.tsx   ← write first
  src/components/habits/HabitCard.tsx        ← implement

  tests/unit/components/StreakBadge.test.tsx
  src/components/habits/StreakBadge.tsx

  tests/unit/components/TOTPSetup.test.tsx
  src/components/auth/TOTPSetup.tsx

Step 4 — Playwright E2E
  tests/e2e/auth.spec.ts      (register, login, 2FA)
  tests/e2e/habits.spec.ts    (create, check-in, streak)
  tests/e2e/settings.spec.ts  (ntfy config, 2FA management)
```

### Scaffold command to run first

```bash
cd d:/repos/habitflow
pnpm create vite frontend --template react-ts
cd frontend
pnpm install
```

Then install all specified deps:

```bash
# Runtime deps
pnpm add \
  zustand \
  @tanstack/react-query \
  react-hook-form \
  zod \
  @hookform/resolvers \
  recharts \
  axios \
  react-router-dom \
  react-i18next \
  i18next \
  i18next-browser-languagedetector \
  date-fns

# Tailwind v4 + shadcn
pnpm add -D \
  tailwindcss \
  @tailwindcss/vite \
  vite-plugin-pwa \
  workbox-window

# Dev / test
pnpm add -D \
  vitest \
  @vitest/coverage-v8 \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  msw \
  jsdom \
  @playwright/test \
  eslint \
  prettier \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin

# shadcn/ui init (run after tailwind setup)
pnpm dlx shadcn@latest init
```

### Key config notes

- `vitest.config.ts`: `environment: 'jsdom'`, `coverage.provider: 'v8'`, `coverage.threshold: 80`
- `playwright.config.ts`: Chromium + Firefox, baseURL pointing to the frontend dev server
- `vite.config.ts`: `@tailwindcss/vite` plugin, `vite-plugin-pwa`, proxy `/api` → `http://localhost:8000`
- `tsconfig.json`: `"strict": true`, path alias `@/*` → `./src/*`

### Key type definitions (src/types/index.ts)

```typescript
export interface User {
  id: string;
  email: string;
  username: string;
  timezone: string;
  totp_enabled: boolean;
  is_active: boolean;
}

export interface Habit {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  color: string;
  icon: string;
  frequency: 'daily' | 'weekly';
  target_days: number[];
  notify_time: string | null;
  is_active: boolean;
  sort_order: number;
  current_streak?: number;
  longest_streak?: number;
}

export interface HabitLog {
  id: string;
  habit_id: string;
  user_id: string;
  log_date: string;
  completed: boolean;
  note: string | null;
}

export interface TodayStatus {
  habit_id: string;
  name: string;
  completed: boolean;
  log_id: string | null;
}

export interface StatsResponse {
  total_days: number;
  completed_days: number;
  completion_rate: number;
  weekly_average: number;
}
```

### utils.ts functions to implement (and test first)

```typescript
// cn(...) — merge Tailwind class names (uses clsx + tailwind-merge)
cn('px-4 py-2', 'text-red-500')

// formatStreak(n) — "🔥 5 day streak" / "🔥 1 day streak" / "" for 0
formatStreak(5) // "🔥 5 day streak"
formatStreak(1) // "🔥 1 day streak"
formatStreak(0) // ""

// formatDate(isoDate) — "Mon, Apr 7" style
formatDate('2026-04-07') // "Mon, Apr 7"

// isToday(isoDate) — boolean
isToday('2026-04-09') // true (if today is 2026-04-09)
```

### Environment variable

```bash
# frontend/.env.local (gitignored)
VITE_API_URL=http://localhost:8000
```

---

## Backend test DB setup reminder

If you need to run backend tests on the new machine:

```bash
# Start test DB container
docker run -d \
  --name habitflow-test-db \
  -e POSTGRES_DB=habitflow_test \
  -e POSTGRES_USER=habitflow \
  -e POSTGRES_PASSWORD=habitflow \
  -p 5433:5432 \
  postgres:16-alpine

# Activate venv and run tests
cd d:/repos/habitflow/backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest
```

---

## Commit convention reminder

```
feat(frontend): add utils with cn, formatStreak, formatDate helpers (TDD step 1)
test(habits): add HabitCard component test
fix(ci): ...
```

---

## GitHub repo

https://github.com/qtekfun/habitflow

Branch: `master` (main branch)
