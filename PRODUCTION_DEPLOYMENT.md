# Production Deployment — GamerCircle / GameConnect

End-to-end guide for the **Render-hosted API**, **Flutter app**, and **Angular admin panel**.

---

## 1. Live environment

| Resource | Value |
|---|---|
| API (web) | `https://gamer-circle-api.onrender.com` |
| API prefix | `/api/v1` |
| Health | `GET /health` |
| Readiness | `GET /ready` (DB + Redis + config flags) |
| Postgres | Render `gamer-circle-db` (PostGIS via start script) |
| Redis | Render `gamer-circle-redis` |
| Region | Oregon (`render.yaml`) |
| Branch | `sit` |
| Service name | `gamer-circle-api` |

Flutter / Angular base URL:

```
https://gamer-circle-api.onrender.com/api/v1
```

---

## 2. Render environment variables

Set in **Dashboard → gamer-circle-api → Environment**.

### Required (core)

| Key | Production value |
|---|---|
| `APP_ENV` | `prod` |
| `DEBUG` | `false` |
| `JWT_SECRET_KEY` | ≥32 random chars (`generateValue` in Blueprint) |
| `DATABASE_URL` | from `gamer-circle-db` (Internal URL) |
| `REDIS_URL` | from `gamer-circle-redis` |
| `CORS_ORIGINS` | `*` (or explicit list including admin origins) |
| `ALLOWED_HOSTS` | `gamer-circle-api.onrender.com,*.onrender.com,localhost` |
| `OTP_DEV_BYPASS_CODE` | **empty** |
| `AUTH_METHODS` | `whatsapp_otp,password` |
| `LOG_LEVEL` | `INFO` |
| `LOG_JSON` | `true` |
| `SEED_ON_BOOT` | `1` |

### Required for real WhatsApp OTP

| Key | Notes |
|---|---|
| `TWILIO_ACCOUNT_SID` | `ACxxxx` |
| `TWILIO_AUTH_TOKEN` | secret |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+1…` (sandbox or approved sender) |

Without Twilio, password login still works; OTP login fails.

### Optional

| Key | Notes |
|---|---|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_S3_BUCKET` | DMS media uploads |
| `AWS_REGION` | default `ap-south-1` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | payments |
| `FORCE_SEED` | `1` once to re-seed demo data |

Full template: `backend/.env.example`.

---

## 3. Migrations on Render

`scripts/render-start.sh` runs automatically on every deploy:

1. Wait for Postgres  
2. `CREATE EXTENSION IF NOT EXISTS postgis`  
3. `alembic upgrade head`  
4. Seed if `gaming_places` empty + always ensure `admin` user  
5. Start uvicorn on `$PORT`

Manual (Render Shell):

```bash
cd /opt/render/project/src   # or service rootDir backend
alembic upgrade head
python scripts/seed_render_bootstrap.py   # full demo (optional)
```

---

## 4. Flutter base URL

Default is **Render production** (`AppConstants.renderBaseUrl`).

```bash
cd frontend/gamer_circle

# Production APK (default URL already Render)
flutter build apk --release \
  --dart-define=APP_FLAVOR=prod \
  --dart-define=API_BASE_URL=https://gamer-circle-api.onrender.com/api/v1

# Local backend
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1 \
  --dart-define=APP_FLAVOR=dev
```

Release builds: Dio logs off, `debugPrint` no-op, HTTPS-only network config.

---

## 5. Angular admin base URL

| File | URL |
|---|---|
| `environment.ts` (dev) | `http://localhost:8000/api/v1` |
| `environment.prod.ts` | `https://gamer-circle-api.onrender.com/api/v1` |

```bash
cd admin-microservice-complete/frontend
npm ci
npm start                    # uses environment.ts → local API
npm run build -- --configuration=production
```

Production has `useMockFallback: false` — failed API calls surface as errors (no silent mock data).

**Admin login (after seed):** `admin` / `Admin@123`  
**Demo user:** `lens_by_manish` or `+919999999010` / `Demo@123`

---

## 6. Smoke test the live system

```bash
cd backend
# macOS Python may need --insecure if system CA store is incomplete
python scripts/prod_smoke_test.py --base https://gamer-circle-api.onrender.com --insecure

# With real credentials if defaults differ
python scripts/prod_smoke_test.py \
  --base https://gamer-circle-api.onrender.com \
  --admin-user admin --admin-pass Admin@123 \
  --user-phone +919999999010 --user-pass Demo@123 \
  --insecure
```

Quick curls (allow 60–90s on free-tier cold start):

```bash
curl -sS -m 120 https://gamer-circle-api.onrender.com/health
curl -sS -m 60  https://gamer-circle-api.onrender.com/ready
curl -sS -m 60  https://gamer-circle-api.onrender.com/api/v1/cities
```

---

## 7. End-to-end manual test script

### A. Admin (Angular)

1. Open admin app (prod build or `ng serve` pointed at Render).  
2. Login: `admin` / `Admin@123`.  
3. Dashboard stats load from live DB.  
4. **Parlors** → create parlor → verify → assign owner (manager).  
5. Soft-delete parlor → confirm hidden from public list → restore.  
6. **Users** → search demo users; toggle active.  
7. **Gaming bookings / slots / offers** → list and edit status.

### B. Manager

1. Admin assigns owner_id on a parlor to a user with `parlor_owner` role.  
2. That user logs in (Flutter or password API).  
3. Manager analytics / parlor-scoped data only (enforced server-side).

### C. Flutter user

1. Install release APK (Render URL baked in).  
2. **Password path:** `+919999999010` / `Demo@123` (or username `lens_by_manish`).  
3. **OTP path:** request OTP → WhatsApp (requires Twilio) → verify → home.  
4. Home / nearby parlors → open parlor → pick slot → create booking → My Bookings.  
5. Feed, profile, messaging smoke-check.

### D. Auth negative tests

1. Invalid password → 401.  
2. Invalid JWT on `/auth/me` → 401.  
3. Non-admin on `/admin/stats` → 403.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/health` hangs 60–180s | Free tier cold start / suspended service | Wait; confirm service is **Live** in Render Dashboard; upgrade plan if needed |
| `/ready` → database false | `DATABASE_URL` wrong or DB expired | Re-link Postgres; check Internal URL |
| OTP fails in prod | Missing Twilio env | Set `TWILIO_*`; leave `OTP_DEV_BYPASS_CODE` empty |
| Admin shows fake data | Old build with mock fallback | Rebuild with `environment.prod.ts` (`useMockFallback: false`) |
| Admin CORS errors | Browser origin blocked | Set `CORS_ORIGINS=*` or add admin origin |
| 400 Bad Host | `ALLOWED_HOSTS` too strict | Include service hostname / `*.onrender.com` |
| Empty parlors | Seed never ran | `FORCE_SEED=1` redeploy or Shell: `python scripts/seed_render_bootstrap.py` |
| Flutter can't reach API | Wrong `API_BASE_URL` or cleartext | Use HTTPS Render URL; release uses HTTPS-only |

---

## 9. Deploy checklist

- [ ] Push `sit` → Render auto-deploy  
- [ ] Dashboard: Twilio + AWS secrets set  
- [ ] `APP_ENV=prod`, `OTP_DEV_BYPASS_CODE` empty  
- [ ] `/health` and `/ready` OK after cold start  
- [ ] `python scripts/prod_smoke_test.py --base …`  
- [ ] Flutter release APK with Render URL  
- [ ] Angular production build against Render  
- [ ] Admin login + parlor CRUD + Flutter booking smoke  

---

## 10. Architecture notes

- Single FastAPI serves Flutter **and** Angular (`/api/v1/admin/*` requires `ADMIN` role).  
- Soft-delete: parlors (`is_deleted` / `is_active` on extensions), users (`is_active=false`).  
- Files: S3 presigned via DMS (not local disk on Render).  
- Free tier: ~15 min idle spin-down; first request can take 30–90s.
