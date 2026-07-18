#!/usr/bin/env python3
"""Provision GamerCircle on Render via curl (avoids broken system Python SSL)."""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time

API = "https://api.render.com/v1"
REPO = "https://github.com/gamercircle007-art/GamerArena"
BRANCH = "sit"
REGION = "oregon"
PG_NAME = "gamer-circle-db"
REDIS_NAME = "gamer-circle-redis"
SVC_NAME = "gamer-circle-api"


def die(msg: str, code: int = 1) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(code)


def api(method: str, path: str, body: object | None = None, key: str = "") -> object:
    url = f"{API}{path}"
    cmd = [
        "curl",
        "-sS",
        "-X",
        method,
        "-H",
        f"Authorization: Bearer {key}",
        "-H",
        "Accept: application/json",
        "-H",
        "Content-Type: application/json",
        "--max-time",
        "120",
    ]
    if body is not None:
        cmd.extend(["-d", json.dumps(body)])
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed: {r.stderr}")
    raw = r.stdout.strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"bad json: {raw[:500]}") from e
    # surface HTTP errors embedded by Render in body
    if isinstance(data, dict) and data.get("message") and (
        "Unauthorized" in str(data.get("message"))
        or data.get("id") is None
        and path.startswith("/postgres") is False
        and method == "POST"
        and "error" in json.dumps(data).lower()
    ):
        pass
    return data


def unwrap_list(data: object) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items") or []
    return []


def main() -> None:
    key = os.environ.get("RENDER_API_KEY", "").strip()
    if not key:
        die("Set RENDER_API_KEY")

    print("==> Owners")
    owners = unwrap_list(api("GET", "/owners?limit=20", key=key))
    if not owners:
        die("No owners")
    owner = owners[0].get("owner") or owners[0]
    owner_id = owner["id"]
    print(f"    {owner.get('name')} ({owner_id})")

    # --- Postgres ---
    print(f"==> Postgres {PG_NAME}")
    pg_id = None
    for it in unwrap_list(api("GET", "/postgres?limit=50", key=key)):
        p = it.get("postgres") or it
        if p.get("name") == PG_NAME:
            pg_id = p["id"]
            print(f"    exists {pg_id}")
            break
    if not pg_id:
        for plan in ("free", "basic_256mb"):
            body: dict = {
                "name": PG_NAME,
                "ownerId": owner_id,
                "plan": plan,
                "region": REGION,
                "version": "16",
                "databaseName": "gamer_circle",
                "databaseUser": "gamer_circle",
            }
            if plan != "free":
                body["diskSizeGB"] = 1
            print(f"    creating plan={plan}...")
            created = api("POST", "/postgres", body, key=key)
            print(f"    response keys: {list(created) if isinstance(created, dict) else type(created)}")
            if isinstance(created, dict):
                print(json.dumps({k: created.get(k) for k in list(created)[:12]}, indent=2)[:1200])
            pg_id = None
            if isinstance(created, dict):
                pg_id = created.get("id") or (created.get("postgres") or {}).get("id")
            if pg_id:
                print(f"    created {pg_id}")
                break
            print(f"    plan {plan} failed body={json.dumps(created)[:800]}")
        if not pg_id:
            die("Could not create Postgres")

    # --- Redis ---
    print(f"==> Redis {REDIS_NAME}")
    redis_id = None
    redis_list = api("GET", "/redis?limit=50", key=key)
    for it in unwrap_list(redis_list):
        r = it.get("redis") or it
        if r.get("name") == REDIS_NAME:
            redis_id = r["id"]
            print(f"    exists {redis_id}")
            break
    if not redis_id:
        for plan in ("free", "starter"):
            body = {
                "name": REDIS_NAME,
                "ownerId": owner_id,
                "plan": plan,
                "region": REGION,
                "ipAllowList": [],
            }
            print(f"    creating redis plan={plan}...")
            created = api("POST", "/redis", body, key=key)
            print(json.dumps(created, indent=2)[:1200] if isinstance(created, dict) else created)
            redis_id = None
            if isinstance(created, dict):
                redis_id = created.get("id") or (created.get("redis") or {}).get("id")
            if redis_id:
                print(f"    created {redis_id}")
                break
        if not redis_id:
            print("    WARN: continuing without Redis")

    def wait_pg_url(timeout: int = 420) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = api("GET", f"/postgres/{pg_id}", key=key)
            if not isinstance(info, dict):
                time.sleep(8)
                continue
            ci = info.get("connectionInfo") or {}
            url = (
                ci.get("internalConnectionString")
                or ci.get("externalConnectionString")
                or ""
            )
            status = info.get("status")
            print(f"    pg status={status} url={'yes' if url else 'no'}")
            if url:
                return url
            time.sleep(10)
        return ""

    def wait_redis_url(timeout: int = 180) -> str:
        if not redis_id:
            return ""
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = api("GET", f"/redis/{redis_id}", key=key)
            if not isinstance(info, dict):
                time.sleep(8)
                continue
            ci = info.get("connectionInfo") or {}
            url = ci.get("internalConnectionString") or ""
            status = info.get("status")
            print(f"    redis status={status} url={'yes' if url else 'no'}")
            if url:
                return url
            time.sleep(8)
        return ""

    print("==> Waiting for connection strings")
    db_url = wait_pg_url()
    redis_url = wait_redis_url()
    if not db_url:
        die("Postgres connection string not ready")

    # --- Web service ---
    print(f"==> Web service {SVC_NAME}")
    svc_id = None
    for it in unwrap_list(api("GET", "/services?limit=50", key=key)):
        s = it.get("service") or it
        if s.get("name") == SVC_NAME:
            svc_id = s["id"]
            print(f"    exists {svc_id}")
            break

    jwt = secrets.token_urlsafe(48)
    env_vars = [
        {"key": "APP_ENV", "value": "staging"},
        {"key": "DEBUG", "value": "false"},
        {"key": "WEB_CONCURRENCY", "value": "1"},
        {"key": "DATABASE_POOL_SIZE", "value": "5"},
        {"key": "DATABASE_MAX_OVERFLOW", "value": "5"},
        {"key": "PYTHON_VERSION", "value": "3.12.8"},
        {"key": "JWT_SECRET_KEY", "value": jwt},
        {"key": "OTP_DEV_BYPASS_CODE", "value": "123456"},
        {"key": "AUTH_METHODS", "value": "whatsapp_otp,password"},
        {"key": "CORS_ORIGINS", "value": "*"},
        {"key": "ALLOWED_HOSTS", "value": "*"},
        {"key": "LOG_LEVEL", "value": "INFO"},
        {"key": "LOG_JSON", "value": "true"},
        {"key": "DATABASE_URL", "value": db_url},
    ]
    if redis_url:
        env_vars.append({"key": "REDIS_URL", "value": redis_url})
    else:
        # fallback empty redis may break OTP — still set localhost to fail loud
        env_vars.append({"key": "REDIS_URL", "value": "redis://localhost:6379/0"})

    if not svc_id:
        bodies = [
            {
                "type": "web_service",
                "name": SVC_NAME,
                "ownerId": owner_id,
                "repo": REPO,
                "autoDeploy": "yes",
                "branch": BRANCH,
                "rootDir": "backend",
                "envVars": env_vars,
                "serviceDetails": {
                    "runtime": "python",
                    "plan": "free",
                    "region": REGION,
                    "healthCheckPath": "/health",
                    "numInstances": 1,
                    "envSpecificDetails": {
                        "buildCommand": (
                            "pip install poetry==1.8.4 && "
                            "poetry config virtualenvs.create false && "
                            "poetry install --only main --no-root"
                        ),
                        "startCommand": "bash scripts/render-start.sh",
                    },
                },
            },
            {
                "type": "web_service",
                "name": SVC_NAME,
                "ownerId": owner_id,
                "repo": REPO,
                "autoDeploy": "yes",
                "branch": BRANCH,
                "rootDir": "backend",
                "envVars": env_vars,
                "serviceDetails": {
                    "env": "python",
                    "plan": "free",
                    "region": REGION,
                    "healthCheckPath": "/health",
                    "numInstances": 1,
                    "envSpecificDetails": {
                        "buildCommand": (
                            "pip install poetry==1.8.4 && "
                            "poetry config virtualenvs.create false && "
                            "poetry install --only main --no-root"
                        ),
                        "startCommand": "bash scripts/render-start.sh",
                    },
                },
            },
        ]
        for i, body in enumerate(bodies):
            print(f"    create attempt {i+1}...")
            created = api("POST", "/services", body, key=key)
            print(json.dumps(created, indent=2)[:2000] if isinstance(created, dict) else str(created)[:2000])
            if isinstance(created, dict):
                svc_id = created.get("id") or (created.get("service") or {}).get("id")
            if svc_id:
                print(f"    created {svc_id}")
                break
        if not svc_id:
            die("Service create failed")
    else:
        print("    updating env vars...")
        # Render accepts PUT array to /env-vars
        resp = api("PUT", f"/services/{svc_id}/env-vars", env_vars, key=key)
        print(f"    env update: {str(resp)[:300]}")

    print("==> Trigger deploy")
    resp = api("POST", f"/services/{svc_id}/deploys", {"clearCache": "do_not_clear"}, key=key)
    print(f"    {str(resp)[:400]}")

    print("==> Waiting for live (up to 20 min)")
    public_url = ""
    for i in range(120):
        info = api("GET", f"/services/{svc_id}", key=key)
        if not isinstance(info, dict):
            time.sleep(10)
            continue
        sd = info.get("serviceDetails") or {}
        public_url = sd.get("url") or info.get("url") or public_url
        deploys = unwrap_list(api("GET", f"/services/{svc_id}/deploys?limit=1", key=key))
        status = "none"
        if deploys:
            d0 = deploys[0].get("deploy") or deploys[0]
            status = d0.get("status") or "unknown"
        print(f"    [{i+1}] status={status} url={public_url or '?'}")
        if status == "live":
            print("\nSUCCESS")
            print(f"API:    {public_url}")
            print(f"Health: {public_url}/health")
            print(f"Docs:   {public_url}/docs")
            hr = subprocess.run(
                ["curl", "-sS", "-m", "90", f"{public_url}/health"],
                capture_output=True,
                text=True,
            )
            print("health:", hr.stdout[:500] or hr.stderr[:300])
            out = {
                "service_id": svc_id,
                "postgres_id": pg_id,
                "redis_id": redis_id,
                "url": public_url,
            }
            path = os.path.join(os.path.dirname(__file__), "..", ".render-deploy.json")
            with open(path, "w") as f:
                json.dump(out, f, indent=2)
            print(f"wrote {path}")
            return
        if status in {"build_failed", "update_failed", "canceled", "deactivated"}:
            die(f"Deploy failed: {status}. https://dashboard.render.com/web/{svc_id}")
        time.sleep(10)

    die(f"Timeout. https://dashboard.render.com/web/{svc_id}")


if __name__ == "__main__":
    main()
