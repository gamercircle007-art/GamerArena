# Production diagnostics (AI-readable)

## Sources of truth

| Layer | Value |
|---|---|
| API | `https://gamer-circle-api.onrender.com` |
| Flutter base | `https://gamer-circle-api.onrender.com/api/v1` |
| Render branch | **`sit` only** (not `main`) |
| Service id | `srv-d9dlbtrtqb8s738uohkg` |
| Dashboard | https://dashboard.render.com/web/srv-d9dlbtrtqb8s738uohkg |

## Error codes (Flutter + API)

| Code | Meaning | Fix |
|---|---|---|
| `E_API_TIMEOUT` | TCP/TLS ok but no HTTP body | Render web Failed/cold → Manual Deploy clear cache |
| `E_API_UNREACHABLE` | No network path to API | Check device network / API URL |
| `E_HTTP_4xx/5xx` | API responded with error | Read `message` from body |
| `E_DB` | `/ready` database false | Link Internal DATABASE_URL |
| `E_REDIS` | `/ready` redis false | Link Redis; OTP needs Redis |
| `E_TWILIO` | Twilio not configured | Set TWILIO_* on Render for WhatsApp OTP |
| `E_VALIDATION` | Bad request body | Fix client payload |

## Probe sequence

```bash
curl -m 20 https://gamer-circle-api.onrender.com/health   # must 200
curl -m 30 https://gamer-circle-api.onrender.com/ready    # 200 or 503+hints
curl -m 30 -X POST https://gamer-circle-api.onrender.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Admin@123"}'
```

## Redeploy

```bash
# git push sit (autoDeploy) + optional Render API clear-cache
bash scripts/redeploy_production.sh

# after /health is 200 — rebuild Flutter APK (deletes old release)
bash scripts/redeploy_production.sh --apk
# or
bash scripts/build_android_render.sh
```

## Failed service recovery

1. Dashboard → gamer-circle-api → **Manual Deploy → Clear build cache & deploy**
2. Logs must show `=== Starting uvicorn` then Live
3. Do **not** rebuild Flutter until step 2 works

## OTP vs password

- Password works without Twilio (`admin` / `Admin@123` after seed)
- OTP requires Live API + Redis + Twilio WhatsApp secrets
