# Why gamer-circle-api fails — analysis + fixes (2026-07-24)

## Evidence (this environment)

| Check | Result |
|---|---|
| DNS / TCP 443 | OK |
| TLS | OK |
| `GET /health` | **Timeout, 0 bytes** |
| `GET /ready` | Never reached |
| Local Render log files | **None** (Render logs only in Dashboard) |
| GitHub **Deploy Render** | **success** (poetry + `import app` OK on Ubuntu 3.12) |
| GitHub CI/Tests | fail for unrelated reasons (not used by Render) |
| Branch | Render = **`sit`** only |
| DB / Redis services | Available (Dashboard) — web service Failed |

**Conclusion:** Edge is up; **origin process never answers HTTP**. Not a Flutter bug. Not Twilio. DB/Redis “Available” does not prove the web process can talk to them.

## Root causes (ranked)

### 1. Free-tier service stuck **Failed** (primary)

Once Failed, health hangs at edge. Auto-deploy from git may not recover without **Manual Deploy → Clear build cache**.

### 2. Start script blocked past health window (likely historical)

Old `render-start.sh` waited on Postgres without hard connect timeouts (asyncpg could hang minutes × N attempts). Render marks deploy Failed if `/health` never passes.

**Fix applied:** default `USE_FULL_BOOT=0` → **pure `uvicorn` only** (binds PORT immediately). Full migrate/seed via `USE_FULL_BOOT=1` later.

### 3. Seed / OOM on free tier

`SEED_ON_BOOT=1` full bootstrap can OOM. **Now default `SEED_ON_BOOT=0`.**

### 4. JWT / settings crash at import

`JWT_SECRET_KEY` min 32. Blueprint has `generateValue: true`. Fallback still in full boot script.

### 5. Not the problem

- Missing local log files (expected)
- Flutter APK (built; needs Live API)
- Twilio (OTP only after Live)
- CI pytest/flutter analyze (does not stop Render deploy)

## What we changed

1. `render.yaml` — `USE_FULL_BOOT=0`, pure uvicorn start; seed off  
2. `scripts/render-start.sh` — hard DB timeouts when full boot used  
3. Flutter `E_*` errors + login API banner  
4. `/ready` returns `hints` + error class names for AI debug  

## Recovery procedure (Dashboard — required)

1. https://dashboard.render.com/web/srv-d9dlbtrtqb8s738uohkg  
2. **Manual Deploy → Clear build cache & deploy** (branch `sit`)  
3. Logs must show: `Uvicorn running on http://0.0.0.0:$PORT`  
4. Status **Live**  
5. Then:

```bash
curl -m 20 https://gamer-circle-api.onrender.com/health
curl -m 30 https://gamer-circle-api.onrender.com/ready
```

6. After Live: set `USE_FULL_BOOT=1` once (or Shell: `alembic upgrade head` + seed), re-deploy.  
7. Set Twilio for OTP. Password: `admin` / `Admin@123` after admin seed.

## Optional API key (so AI can redeploy)

```bash
export RENDER_API_KEY=rnd_...
bash scripts/redeploy_production.sh
```
