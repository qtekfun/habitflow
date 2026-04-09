# Local Development Guide

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://python.org) or pyenv |
| Node.js | 22+ | [nodejs.org](https://nodejs.org) or nvm |
| pnpm | 10+ | `npm install -g pnpm` |
| Docker | any recent | [docs.docker.com](https://docs.docker.com/get-docker/) |

---

## 1. Clone the repo

```bash
git clone https://github.com/qtekfun/habitflow.git
cd habitflow
```

---

## 2. Backend

### 2a. Start the test database

```bash
docker run -d \
  --name habitflow-dev-db \
  -e POSTGRES_DB=habitflow \
  -e POSTGRES_USER=habitflow \
  -e POSTGRES_PASSWORD=habitflow \
  -p 5432:5432 \
  postgres:16-alpine
```

### 2b. Create a virtual environment and install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt -r requirements-dev.txt
```

### 2c. Configure environment variables

```bash
cp ../deploy/.env.example .env
# Edit .env — at minimum set SECRET_KEY:
#   SECRET_KEY=$(openssl rand -hex 32)
#   DATABASE_URL=postgresql+asyncpg://habitflow:habitflow@localhost:5432/habitflow
```

### 2d. Run database migrations

```bash
alembic upgrade head
```

### 2e. Start the API server

```bash
uvicorn app.main:app --reload
# API available at http://localhost:8000
# OpenAPI docs at http://localhost:8000/docs
```

### 2f. Run backend tests

A separate test database on port 5433 is required:

```bash
docker run -d \
  --name habitflow-test-db \
  -e POSTGRES_DB=habitflow_test \
  -e POSTGRES_USER=habitflow \
  -e POSTGRES_PASSWORD=habitflow \
  -p 5433:5432 \
  postgres:16-alpine

pytest                                    # all tests
pytest --cov=app --cov-report=term        # with coverage
pytest tests/unit/                        # unit tests only
pytest tests/integration/                 # integration tests only
```

---

## 3. Frontend

### 3a. Install dependencies

```bash
cd frontend
pnpm install
```

### 3b. Configure environment variables

```bash
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### 3c. Start the dev server

```bash
pnpm dev
# App available at http://localhost:5173
# Requests to /api/* are proxied to http://localhost:8000
```

### 3d. Run frontend unit tests

No backend required — MSW intercepts all API calls.

```bash
pnpm vitest run              # run once
pnpm vitest                  # watch mode
pnpm vitest run --coverage   # with coverage report (opens in browser)
```

### 3e. Run Playwright E2E tests

Requires both the frontend dev server and the backend to be running.

```bash
pnpm playwright install --with-deps chromium firefox   # first time only
pnpm playwright test                                   # all specs
pnpm playwright test --ui                              # interactive UI mode
pnpm playwright test tests/e2e/auth.spec.ts            # single spec
```

---

## 4. Running everything together (quick start)

Open three terminals:

```bash
# Terminal 1 — database
docker start habitflow-dev-db   # or the docker run command from step 2a

# Terminal 2 — backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 3 — frontend
cd frontend && pnpm dev
```

Then open `http://localhost:5173`.

---

## 5. Linting and type checking

### Backend

```bash
cd backend
ruff check .          # lint
ruff format --check . # format check
mypy app/             # type check
```

### Frontend

```bash
cd frontend
pnpm tsc --noEmit     # type check
pnpm eslint .         # lint
pnpm prettier --check . # format check
```

---

## 6. Production build (frontend)

```bash
cd frontend
pnpm build
# Output in frontend/dist/ — served by nginx in Docker
```

---

## 7. Full Docker Compose stack (production-like)

```bash
cd deploy
cp .env.example .env
# Fill in all required values in .env

docker compose up -d
# Frontend: http://localhost (port 80)
# API:      http://localhost:8000
```

See [deployment.md](deployment.md) for the full self-hosting guide.
