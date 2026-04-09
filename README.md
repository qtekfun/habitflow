# HabitFlow

Self-hosted habit tracker. Track daily habits, build streaks, get push notifications via ntfy. Installable as PWA.

## Features

- Daily and weekly habit tracking with streak calculation
- Statistics dashboard with charts and completion rates
- TOTP 2FA (Ente Auth, Aegis, Google Authenticator compatible)
- Push notifications via ntfy (self-hosted or ntfy.sh)
- Installable PWA — no app store needed
- Multi-user, self-hosted first
- Single Docker Compose deployment, zero external dependencies

## Quick start

```bash
git clone https://github.com/qtekfun/habitflow.git
cd habitflow/deploy
cp .env.example .env        # fill in SECRET_KEY and POSTGRES_PASSWORD
docker compose up -d
```

Open `http://localhost` in your browser.

## Local development

See [docs/development.md](docs/development.md) for the full local setup guide covering:

- Backend (FastAPI + PostgreSQL)
- Frontend (React + Vite)
- Running tests (pytest, vitest, Playwright)
- Linting and type checking

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115+, SQLAlchemy 2 async, PostgreSQL 16 |
| Auth | JWT + httpOnly refresh cookie, TOTP (pyotp) |
| Notifications | ntfy via APScheduler |
| Frontend | React 19, TypeScript, Vite 6, Tailwind CSS v4 |
| State | Zustand + TanStack Query v5 |
| PWA | vite-plugin-pwa + Workbox |
| Testing | pytest + vitest + Playwright, ≥80% coverage enforced |
| CI/CD | GitHub Actions, Trivy, Dependabot |

## Contributing

Follow [Conventional Commits](https://www.conventionalcommits.org/). Tests are required — coverage must stay ≥ 80%. See [docs/development.md](docs/development.md).
