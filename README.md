# Paythan Backend (BE-python)

FastAPI modular monolith for Paythan authentication and user services. Backend-only repository with Docker Compose for local and production-like development.

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, Python 3.12+, Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Auth | WhatsApp OTP (Twilio) + password + JWT |

## Project Structure

```
.
├── backend/              # FastAPI application
│   ├── app/              # domains, core, db
│   ├── alembic/          # database migrations
│   ├── Dockerfile        # dev + production stages
│   └── scripts/          # run_dev.py, docker-entrypoint.sh
├── scripts/              # docker-up.sh, run_backend.sh
├── docker-compose.yml    # postgres + redis + backend
├── .env.example          # docker-compose env template
└── README.md
```

## Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose

### 1. Configure environment

```bash
cp .env.example .env

# Generate a secure JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# Paste result into JWT_SECRET_KEY in .env
```

### 2. Start the stack

```bash
bash scripts/docker-up.sh
```

Or manually:

```bash
docker compose up --build -d
```

Migrations run automatically on backend startup. Verify:

```bash
curl http://localhost:8000/health
```

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### 3. Stop

```bash
docker compose down
```

## Quick Start (Local, no Docker)

Uses SQLite + FakeRedis for quick testing:

```bash
bash scripts/run_backend.sh
```

Or:

```bash
cd backend
cp .env.example .env
source .venv/bin/activate
poetry install
python scripts/run_dev.py
```

## Authentication

| Flow | Endpoints |
|------|-----------|
| Signup | `POST /api/v1/auth/signup/request-otp` → `POST /api/v1/auth/signup/verify-otp` |
| Login (OTP) | `POST /api/v1/auth/login/request-otp` → `POST /api/v1/auth/login/verify-otp` |
| Login (password) | `POST /api/v1/auth/login` |
| Session | `GET /api/v1/auth/me`, `POST /api/v1/auth/refresh-token`, `POST /api/v1/auth/logout` |

**Local dev without Twilio:** OTP codes are printed in backend logs.

See [backend/README.md](backend/README.md) for full API examples and environment variable reference.

## Environment Variables

Root `.env` is used by `docker-compose.yml`. Copy from `.env.example`.

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | Yes | 32+ character secret for JWT signing |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:pass@postgres:5432/db` |
| `REDIS_URL` | Yes | `redis://redis:6379/0` |
| `TWILIO_ACCOUNT_SID` | For WhatsApp OTP | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | For WhatsApp OTP | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | For WhatsApp OTP | `whatsapp:+14155238886` (sandbox) |

## Development

```bash
# Infrastructure only (postgres + redis)
docker compose up postgres redis -d

# Backend with Poetry
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

## Testing

```bash
cd backend && poetry run pytest -v
```

## Production Docker Image

```bash
cd backend
docker build --target production -t paythan-backend .
```

## License

Proprietary — Paythan Team