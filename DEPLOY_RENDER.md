# Deploy backend to Render (GitHub)

## What this repo provisions

`render.yaml` Blueprint creates:

| Resource | Name | URL / role | Plan |
|---|---|---|---|
| Web Service | `gamer-circle-api` | `https://gamer-circle-api.onrender.com` | free |
| Static Site | `gamer-circle-admin` | `https://gamer-circle-admin.onrender.com` | free (CDN) |
| Postgres | `gamer-circle-db` | internal + external connection string | free |
| Key Value (Redis) | `gamer-circle-redis` | OTP, sessions, presence | free |

Flutter API base (with `/api/v1`):

```
https://gamer-circle-api.onrender.com/api/v1
```

Angular admin (production build → same API):

```
https://gamer-circle-admin.onrender.com
```

Admin login (after seed): `admin` / `Admin@123` (or demo phones + password).

## Production env (set in Render Dashboard)

| Key | Production value |
|---|---|
| `APP_ENV` | `prod` |
| `DEBUG` | `false` |
| `OTP_DEV_BYPASS_CODE` | *(empty)* |
| `TWILIO_ACCOUNT_SID` | your `ACxxxx` |
| `TWILIO_AUTH_TOKEN` | console secret |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+1...` (sandbox or approved) |
| `AWS_*` | S3 for media (optional until uploads needed) |
| `RAZORPAY_*` | optional payments |

Full production runbook: **`PRODUCTION_DEPLOYMENT.md`** (env vars, migrations, Flutter/Angular URLs, smoke tests, troubleshooting).

Checks (allow 60–90s free-tier cold start):

```bash
curl -sS -m 120 https://gamer-circle-api.onrender.com/health
curl -sS -m 60  https://gamer-circle-api.onrender.com/ready
python backend/scripts/prod_smoke_test.py --base https://gamer-circle-api.onrender.com --insecure
```

`/ready` reports DB/Redis + `twilio_configured` (no secrets).

**Seeded logins (after SEED_ON_BOOT):**  
- Admin: `admin` / `Admin@123`  
- User: `+919999999010` or `lens_by_manish` / `Demo@123`

## One-time setup (you click once)

1. Push this branch (`sit`) to GitHub (already configured: `gamercircle007-art/GamerArena`).
2. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Select repo **GamerArena**, branch **`sit`**, Blueprint file `render.yaml`.
4. Click **Apply** — wait for Postgres + Redis + first Docker build (~5–15 min).
5. Open `https://gamer-circle-api.onrender.com/health` — should return healthy JSON.
6. Swagger (staging): `https://gamer-circle-api.onrender.com/docs`

### Free-tier notes

- Web free tier **spins down after ~15 min idle** — first request after sleep can take 30–60s.
- Free Postgres is fine for testing; expires after 30 days of inactivity on some plans — check dashboard.
- PostGIS is created at startup (`CREATE EXTENSION IF NOT EXISTS postgis`). If your plan blocks it, nearby/geo features fail; auth/feed/booking still work where they don't need geo.

### Demo login after seed (optional)

On Render shell (or one-off job), from service:

```bash
# In Render Dashboard → gamer-circle-api → Shell
python scripts/seed_demo_full.py
```

Default demo users (if seeded): phones `+91999999901X` / password `Demo@123`, OTP bypass `123456`.

## Flutter Android test build

```bash
cd frontend/gamer_circle

flutter build apk --release \
  --dart-define=API_BASE_URL=https://gamer-circle-api.onrender.com/api/v1
```

APK path:

```
build/app/outputs/flutter-apk/app-release.apk
```

Install on device/emulator:

```bash
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

Local dev still defaults to `http://localhost:8000/api/v1` when `--dart-define` is omitted.

## Manual service create (if not using Blueprint)

### 1. Postgres
- New → Postgres → name `gamer-circle-db` → Free → Create

### 2. Key Value
- New → Key Value → name `gamer-circle-redis` → Free → private network only

### 3. Web Service
- New → Web Service → connect GitHub repo → branch `sit`
- Runtime: **Docker**
- Dockerfile path: `backend/Dockerfile`
- Docker context: `backend`
- Docker command: `bash scripts/render-start.sh`
- Health check path: `/health`
- Env vars (link DB + Redis from dashboard dropdowns where possible):

| Key | Value |
|---|---|
| `APP_ENV` | `staging` |
| `JWT_SECRET_KEY` | random ≥32 chars |
| `OTP_DEV_BYPASS_CODE` | `123456` |
| `DATABASE_URL` | from Postgres (Internal Database URL) |
| `REDIS_URL` | from Key Value |
| `WEB_CONCURRENCY` | `1` |
| `CORS_ORIGINS` | `*` |
| `ALLOWED_HOSTS` | `*` |

`DATABASE_URL` is auto-normalized to `postgresql+asyncpg://...` + SSL in app config.

## After deploy — update URL if service name differs

If Render assigns a different hostname, rebuild the APK with the real URL:

```bash
flutter build apk --release \
  --dart-define=API_BASE_URL=https://YOUR-SERVICE.onrender.com/api/v1
```
