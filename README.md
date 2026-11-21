# AutoPredict

Predictive car maintenance for individual owners: an agentic AI backend (FastAPI, AutoGen agents on a local Llama 3 via Ollama), a staff web dashboard (React) and an owner app (Flutter).

Vehicle data is simulated for now (no car hardware). A seeded simulator builds a consistent demo world (owners, cars, service history, bookings, conversations), and every dashboard number is computed from that data in the database.

## Repository layout

| Path | What it is |
| --- | --- |
| `backend/` | API, agents, simulator, migrations, tests |
| `backend/api/` | FastAPI app (`app.py`) and routers |
| `backend/core/` | Settings, security, logging |
| `backend/db/` | SQLAlchemy models and session |
| `backend/domain/` | Rules shared across layers (parts, workshop rules, baseline predictor) |
| `backend/services/` | Diagnosis, scheduling, audit |
| `backend/sim/` | Deterministic demo-world simulator (`python -m sim.build`) |
| `backend/migrations/` | Alembic migrations |
| `autopredict-web/` | Staff dashboard (React + Vite) |
| `autopredict_app/` | Owner app (Flutter) |
| `docs/legacy/` | Older guides, kept for reference |

The agent modules in `backend/*.py` (orchestrator, engagement, learning, …) are the original agent layer. The CLI demo (`python main.py`) still runs them with in-memory state; Phase 1 moves them into the server.

## Quick start (local, no Docker)

Prerequisites: Python 3.11, Node 22, [Ollama](https://ollama.com) with `ollama pull llama3:8b` (only needed for AI chat and LLM diagnosis).

```bash
# 1. Configuration
cp .env.example .env
# Set JWT_SECRET and DEMO_STAFF_PASSWORD in .env:
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 2. Backend
cd backend
python -m venv venv
venv/Scripts/activate            # Windows (Git Bash: source venv/Scripts/activate)
# source venv/bin/activate       # macOS / Linux
pip install -r requirements-dev.txt
alembic upgrade head             # create the database (SQLite file by default)
python -m sim.build              # demo data; prints the demo logins
python webhook_server.py         # http://localhost:8001  (API docs: /docs)

# 3. Web dashboard (new terminal)
cd autopredict-web
npm install
npm run dev                      # http://localhost:5173
```

Sign in to the dashboard with `ops@autopredict.local`, `manager@autopredict.local` or `executive@autopredict.local` and your `DEMO_STAFF_PASSWORD`.

## Quick start (Docker)

```bash
cp .env.example .env             # set JWT_SECRET and DEMO_STAFF_PASSWORD
docker compose up -d --build     # PostgreSQL (pgvector), Redis, API, web
docker compose run --rm api python -m sim.build
```

Dashboard: http://localhost:8080 · API: http://localhost:8001. Ollama is expected on the host (`host.docker.internal:11434`); `docker compose --profile ollama up -d` runs it in a container instead.

## Mobile app

```bash
cd autopredict_app
flutter pub get
# Android emulator (default points at the host machine):
flutter run
# Physical phone on the same Wi-Fi:
flutter run --dart-define=API_BASE_URL=http://<your-PC-LAN-IP>:8001/api
```

Owners sign in with their phone number and a one-time code. With no SMS provider configured (development), the code is returned by the API and shown on the login screen as "Dev code". `python -m sim.build` prints a few demo owner phone numbers.

## Demo data

```bash
python -m sim.build --seed 42                          # first build
python -m sim.build --seed 42 --reset                  # wipe and rebuild (refused when ENV=prod)
python -m sim.build --as-of 2026-11-21T12:00           # pin the clock for repeatable demos
python -m sim.build --owners 200 --vehicles 300        # smaller world
```

Same seed and as-of time give the same world. Service intervals, part lifetimes and prices in `backend/sim/catalogue.py` are approximate placeholders; replace them with owner's-manual figures and a real price list.

## Development

```bash
cd backend
python -m pytest -q                       # API, domain, simulator tests (SQLite)
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host/empty_db python -m pytest -q   # same suite on PostgreSQL
ruff check . && ruff format --check .

cd ../autopredict-web && npm run lint && npm run build
cd ../autopredict_app && flutter analyze && flutter test
```

Pre-commit hooks (run from the repository root): `pip install pre-commit && pre-commit install`. CI (`.github/workflows/ci.yml`) runs the backend suite on SQLite and PostgreSQL, the web lint and build, and the Flutter analyzer and tests.

## Configuration

All settings live in `.env` (see `.env.example`) and are read by `backend/core/settings.py`. Notable ones:

| Variable | Purpose |
| --- | --- |
| `ENV` | `dev`, `test` or `prod`. `prod` requires a strong `JWT_SECRET`, PostgreSQL and an SMS provider for OTP |
| `DATABASE_URL` | Defaults to a local SQLite file; use `postgresql+asyncpg://…` in production |
| `REDIS_URL` | Optional; enables WebSocket events across several API workers |
| `JWT_SECRET` | Signs access tokens (32+ random characters) |
| `DEMO_STAFF_PASSWORD` | Password for the demo staff accounts created by `sim.build` |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Local LLM |
| `TWILIO_*`, `SMTP_*` | Channels; empty means simulation mode |
| `PLATFORM_MONTHLY_COST_INR` | Used by the ROI view |
| `VITE_API_URL` | (web build) API address baked into the dashboard |
| `API_BASE_URL` | (Flutter `--dart-define`) API address for the app |
