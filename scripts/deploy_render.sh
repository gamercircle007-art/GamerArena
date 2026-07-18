#!/usr/bin/env bash
# Fully provision GamerCircle on Render via API.
# Usage:
#   export RENDER_API_KEY=rnd_...
#   bash scripts/deploy_render.sh
set -euo pipefail

API="https://api.render.com/v1"
REPO="https://github.com/gamercircle007-art/GamerArena"
BRANCH="sit"
REGION="oregon"

if [[ -z "${RENDER_API_KEY:-}" ]]; then
  echo "ERROR: Set RENDER_API_KEY first."
  echo "Create one: https://dashboard.render.com/u/settings#api-keys"
  echo "Then:  export RENDER_API_KEY=rnd_xxxxx"
  echo "       bash scripts/deploy_render.sh"
  exit 1
fi

auth=(-H "Authorization: Bearer ${RENDER_API_KEY}" -H "Accept: application/json" -H "Content-Type: application/json")

echo "==> Fetching owner / workspace..."
OWNERS_JSON=$(curl -sS "${auth[@]}" "${API}/owners?limit=20")
OWNER_ID=$(python3 - <<PY
import json,sys
data=json.loads('''${OWNERS_JSON}'''.replace("'''","'"))
# response is list of {owner: {...}, cursor}
items = data if isinstance(data, list) else data.get("items") or data
oid=None
for it in items:
    o = it.get("owner", it)
    if o.get("type") in ("team","user") or o.get("id"):
        oid = o.get("id")
        print(f"Using owner: {o.get('name') or o.get('email') or oid} ({oid})", file=sys.stderr)
        break
if not oid:
    print(json.dumps(data, indent=2)[:2000], file=sys.stderr)
    sys.exit("No owner found")
print(oid)
PY
)

echo "Owner: ${OWNER_ID}"

# Helper: find existing resource by name
find_postgres() {
  local name="$1"
  curl -sS "${auth[@]}" "${API}/postgres?limit=50" | python3 -c "
import json,sys
name=sys.argv[1]
data=json.load(sys.stdin)
items=data if isinstance(data,list) else data.get('items',[])
for it in items:
  p=it.get('postgres',it)
  if p.get('name')==name:
    print(p.get('id','')); break
" "$name"
}

find_service() {
  local name="$1"
  curl -sS "${auth[@]}" "${API}/services?limit=50" | python3 -c "
import json,sys
name=sys.argv[1]
data=json.load(sys.stdin)
items=data if isinstance(data,list) else data.get('items',[])
for it in items:
  s=it.get('service',it)
  if s.get('name')==name:
    print(s.get('id','')); break
" "$name"
}

echo "==> Postgres (gamer-circle-db)..."
PG_ID=$(find_postgres "gamer-circle-db" || true)
if [[ -n "${PG_ID}" ]]; then
  echo "Already exists: ${PG_ID}"
else
  PG_RESP=$(curl -sS -X POST "${auth[@]}" "${API}/postgres" -d "{
    \"name\": \"gamer-circle-db\",
    \"ownerId\": \"${OWNER_ID}\",
    \"plan\": \"free\",
    \"region\": \"${REGION}\",
    \"version\": \"16\",
    \"databaseName\": \"gamer_circle\",
    \"databaseUser\": \"gamer_circle\"
  }")
  echo "${PG_RESP}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d,indent=2)[:1500])"
  PG_ID=$(echo "${PG_RESP}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id') or d.get('postgres',{}).get('id') or '')")
  if [[ -z "${PG_ID}" ]]; then
    echo "Postgres free plan failed — trying basic_256mb..."
    PG_RESP=$(curl -sS -X POST "${auth[@]}" "${API}/postgres" -d "{
      \"name\": \"gamer-circle-db\",
      \"ownerId\": \"${OWNER_ID}\",
      \"plan\": \"basic_256mb\",
      \"region\": \"${REGION}\",
      \"version\": \"16\",
      \"databaseName\": \"gamer_circle\",
      \"databaseUser\": \"gamer_circle\",
      \"diskSizeGB\": 1
    }")
    echo "${PG_RESP}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d,indent=2)[:1500])"
    PG_ID=$(echo "${PG_RESP}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id') or d.get('postgres',{}).get('id') or '')")
  fi
  [[ -n "${PG_ID}" ]] || { echo "FATAL: could not create Postgres"; exit 1; }
fi
echo "Postgres ID: ${PG_ID}"

echo "==> Key Value / Redis (gamer-circle-redis)..."
KV_ID=$(find_service "gamer-circle-redis" || true)
# Also search redis endpoint
if [[ -z "${KV_ID}" ]]; then
  KV_ID=$(curl -sS "${auth[@]}" "${API}/redis?limit=50" 2>/dev/null | python3 -c "
import json,sys
try:
  data=json.load(sys.stdin)
except Exception:
  sys.exit(0)
items=data if isinstance(data,list) else data.get('items',[])
for it in items:
  r=it.get('redis',it)
  if r.get('name')=='gamer-circle-redis':
    print(r.get('id','')); break
" || true)
fi

if [[ -n "${KV_ID}" ]]; then
  echo "Redis already exists: ${KV_ID}"
else
  # Try redis endpoint (legacy name for keyvalue)
  KV_RESP=$(curl -sS -X POST "${auth[@]}" "${API}/redis" -d "{
    \"name\": \"gamer-circle-redis\",
    \"ownerId\": \"${OWNER_ID}\",
    \"plan\": \"free\",
    \"region\": \"${REGION}\",
    \"ipAllowList\": []
  }" 2>&1) || true
  echo "${KV_RESP}" | python3 -c "import json,sys
try:
  d=json.load(sys.stdin); print(json.dumps(d,indent=2)[:1500])
except Exception as e:
  print(sys.stdin.read() if False else open(0).read() if False else '')
" 2>/dev/null || echo "${KV_RESP}" | head -c 1500
  KV_ID=$(echo "${KV_RESP}" | python3 -c "import json,sys
try:
  d=json.load(sys.stdin); print(d.get('id') or d.get('redis',{}).get('id') or '')
except: print('')" || true)
fi
echo "Redis ID: ${KV_ID:-pending}"

echo "==> Waiting for Postgres connection string..."
for i in $(seq 1 36); do
  PG_INFO=$(curl -sS "${auth[@]}" "${API}/postgres/${PG_ID}")
  DB_URL=$(echo "${PG_INFO}" | python3 -c "import json,sys
d=json.load(sys.stdin)
print(d.get('connectionInfo',{}).get('internalConnectionString')
  or d.get('connectionInfo',{}).get('externalConnectionString')
  or d.get('internalConnectionString')
  or d.get('database',{}).get('connectionString')
  or '')" 2>/dev/null || true)
  STATUS=$(echo "${PG_INFO}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status') or d.get('postgres',{}).get('status') or '')" 2>/dev/null || true)
  echo "  attempt $i status=${STATUS} url=${DB_URL:+set}"
  if [[ -n "${DB_URL}" ]]; then break; fi
  sleep 10
done
if [[ -z "${DB_URL}" ]]; then
  echo "WARN: no connection string yet; will link via env fromDatabase after service create"
fi

REDIS_URL=""
if [[ -n "${KV_ID}" ]]; then
  for i in $(seq 1 18); do
    R_INFO=$(curl -sS "${auth[@]}" "${API}/redis/${KV_ID}" 2>/dev/null || true)
    REDIS_URL=$(echo "${R_INFO}" | python3 -c "import json,sys
try:
 d=json.load(sys.stdin)
 print(d.get('connectionInfo',{}).get('internalConnectionString') or d.get('connectionString') or '')
except: print('')" 2>/dev/null || true)
    [[ -n "${REDIS_URL}" ]] && break
    sleep 5
  done
fi

JWT=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

echo "==> Web service (gamer-circle-api)..."
SVC_ID=$(find_service "gamer-circle-api" || true)
if [[ -n "${SVC_ID}" ]]; then
  echo "Service already exists: ${SVC_ID}"
else
  # Build env vars JSON
  ENV_JSON=$(python3 - <<PY
import json
envs = [
  {"key":"APP_ENV","value":"staging"},
  {"key":"DEBUG","value":"false"},
  {"key":"WEB_CONCURRENCY","value":"1"},
  {"key":"DATABASE_POOL_SIZE","value":"5"},
  {"key":"DATABASE_MAX_OVERFLOW","value":"5"},
  {"key":"PYTHON_VERSION","value":"3.12.8"},
  {"key":"JWT_SECRET_KEY","value":"${JWT}"},
  {"key":"OTP_DEV_BYPASS_CODE","value":"123456"},
  {"key":"AUTH_METHODS","value":"whatsapp_otp,password"},
  {"key":"CORS_ORIGINS","value":"*"},
  {"key":"ALLOWED_HOSTS","value":"*"},
  {"key":"LOG_LEVEL","value":"INFO"},
  {"key":"LOG_JSON","value":"true"},
]
db_url = """${DB_URL}"""
redis_url = """${REDIS_URL}"""
pg_id = """${PG_ID}"""
kv_id = """${KV_ID}"""
if db_url:
  envs.append({"key":"DATABASE_URL","value":db_url})
elif pg_id:
  envs.append({"key":"DATABASE_URL","fromDatabase":{"name":"gamer-circle-db","property":"connectionString"}})
# fromDatabase only works in blueprints; for API use value
if redis_url:
  envs.append({"key":"REDIS_URL","value":redis_url})
print(json.dumps(envs))
PY
)

  SVC_BODY=$(python3 - <<PY
import json
body = {
  "type": "web_service",
  "name": "gamer-circle-api",
  "ownerId": "${OWNER_ID}",
  "repo": "${REPO}",
  "autoDeploy": "yes",
  "branch": "${BRANCH}",
  "serviceDetails": {
    "env": "python",
    "envSpecificDetails": {
      "buildCommand": "pip install poetry==1.8.4 && poetry config virtualenvs.create false && poetry install --only main --no-root",
      "startCommand": "bash scripts/render-start.sh"
    },
    "plan": "free",
    "region": "${REGION}",
    "healthCheckPath": "/health",
    "numInstances": 1,
  },
  "rootDir": "backend",
  "envVars": json.loads('''${ENV_JSON}''')
}
print(json.dumps(body))
PY
)

  SVC_RESP=$(curl -sS -X POST "${auth[@]}" "${API}/services" -d "${SVC_BODY}")
  echo "${SVC_RESP}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d,indent=2)[:2500])"
  SVC_ID=$(echo "${SVC_RESP}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id') or d.get('service',{}).get('id') or '')")
  [[ -n "${SVC_ID}" ]] || { echo "FATAL: service create failed"; exit 1; }
fi
echo "Service ID: ${SVC_ID}"

# If redis created late, patch env
if [[ -n "${REDIS_URL}" ]]; then
  echo "==> Patching REDIS_URL..."
  curl -sS -X PUT "${auth[@]}" "${API}/services/${SVC_ID}/env-vars/REDIS_URL" \
    -d "{\"value\":\"${REDIS_URL}\"}" | head -c 400 || true
  echo
fi
if [[ -n "${DB_URL}" ]]; then
  echo "==> Patching DATABASE_URL..."
  curl -sS -X PUT "${auth[@]}" "${API}/services/${SVC_ID}/env-vars/DATABASE_URL" \
    -d "{\"value\":\"${DB_URL}\"}" | head -c 400 || true
  echo
fi

echo "==> Trigger deploy..."
curl -sS -X POST "${auth[@]}" "${API}/services/${SVC_ID}/deploys" -d '{"clearCache":"do_not_clear"}' | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d,indent=2)[:800])" || true

echo
echo "==> Waiting for live deploy (up to ~15 min)..."
for i in $(seq 1 90); do
  INFO=$(curl -sS "${auth[@]}" "${API}/services/${SVC_ID}")
  URL=$(echo "${INFO}" | python3 -c "import json,sys
d=json.load(sys.stdin)
sd=d.get('serviceDetails') or d.get('service',{}).get('serviceDetails') or {}
print(sd.get('url') or d.get('url') or '')" 2>/dev/null || true)
  SUSP=$(echo "${INFO}" | python3 -c "import json,sys
d=json.load(sys.stdin)
print(d.get('suspended') or '')" 2>/dev/null || true)
  DEP=$(curl -sS "${auth[@]}" "${API}/services/${SVC_ID}/deploys?limit=1")
  STATUS=$(echo "${DEP}" | python3 -c "import json,sys
d=json.load(sys.stdin)
items=d if isinstance(d,list) else d.get('items',[])
if not items:
  print('none'); raise SystemExit
it=items[0].get('deploy',items[0])
print(it.get('status',''))" 2>/dev/null || echo "unknown")
  echo "  [$i] deploy=${STATUS} url=${URL:-?} suspended=${SUSP}"
  if [[ "${STATUS}" == "live" ]]; then
    echo
    echo "SUCCESS. API: ${URL}"
    echo "Health: ${URL}/health"
    echo "Docs:   ${URL}/docs"
    # probe health
    sleep 5
    curl -sS -m 60 "${URL}/health" || true
    echo
    exit 0
  fi
  if [[ "${STATUS}" == "build_failed" || "${STATUS}" == "update_failed" || "${STATUS}" == "canceled" ]]; then
    echo "Deploy failed with status=${STATUS}"
    exit 1
  fi
  sleep 10
done
echo "Timed out waiting for live. Check dashboard: https://dashboard.render.com/web/${SVC_ID}"
exit 1
