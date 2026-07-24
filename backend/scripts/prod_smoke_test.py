#!/usr/bin/env python3
"""Production smoke tests against a live Render (or local) API.

Usage:
  python scripts/prod_smoke_test.py
  python scripts/prod_smoke_test.py --base https://gamer-circle-api.onrender.com
  python scripts/prod_smoke_test.py --base https://gamer-circle-api.onrender.com \\
      --admin-user admin --admin-pass Admin@123 \\
      --user-phone +919999999010 --user-pass Demo@123

Exit code 0 = all critical checks passed; 1 = one or more failures.
"""
from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""
    status: int | None = None


@dataclass
class Report:
    results: list[Result] = field(default_factory=list)

    def add(self, r: Result) -> None:
        self.results.append(r)
        mark = "OK  " if r.ok else "FAIL"
        status = f" HTTP {r.status}" if r.status is not None else ""
        print(f"[{mark}] {r.name}{status}: {r.detail}")

    @property
    def passed(self) -> bool:
        return all(r.ok for r in self.results)


def make_ctx(insecure: bool) -> ssl.SSLContext | None:
    if not insecure:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def request(
    method: str,
    url: str,
    *,
    body: dict | None = None,
    token: str | None = None,
    timeout: float = 90,
    insecure: bool = False,
    origin: str | None = None,
) -> tuple[int, Any, dict[str, str]]:
    data = None
    headers = {"Accept": "application/json", "User-Agent": "GamerCircle-Smoke/1.0"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if origin:
        headers["Origin"] = origin
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = make_ctx(insecure)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"_raw": raw[:500]}
            return resp.status, payload, dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"_raw": raw[:500]}
        return e.code, payload, dict(e.headers or {})
    except Exception as e:  # noqa: BLE001
        return 0, {"error": f"{type(e).__name__}: {e}"}, {}


def main() -> int:
    p = argparse.ArgumentParser(description="Live API production smoke tests")
    p.add_argument(
        "--base",
        default="https://gamer-circle-api.onrender.com",
        help="API origin (no /api/v1 suffix)",
    )
    p.add_argument("--admin-user", default="admin")
    p.add_argument("--admin-pass", default="Admin@123")
    p.add_argument("--user-phone", default="+919999999010")
    p.add_argument("--user-pass", default="Demo@123")
    p.add_argument("--user-username", default="lens_by_manish")
    p.add_argument("--insecure", action="store_true", help="Skip TLS verify (local CA issues)")
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()

    base = args.base.rstrip("/")
    api = f"{base}/api/v1"
    report = Report()
    insecure = args.insecure

    # 1. Health
    t0 = time.time()
    status, body, _ = request("GET", f"{base}/health", timeout=args.timeout, insecure=insecure)
    report.add(
        Result(
            "Server Health",
            status == 200 and (body.get("status") in ("healthy", "ok")),
            f"{body} ({time.time()-t0:.1f}s)",
            status,
        )
    )

    # 2. Ready (DB + Redis)
    status, body, _ = request("GET", f"{base}/ready", timeout=args.timeout, insecure=insecure)
    db_ok = bool((body.get("checks") or {}).get("database")) if isinstance(body, dict) else False
    redis_ok = bool((body.get("checks") or {}).get("redis")) if isinstance(body, dict) else False
    # Accept degraded redis if DB up (free tier) — still mark redis separately
    report.add(
        Result(
            "Database Connection",
            status in (200, 503) and (db_ok or body.get("status") == "ready"),
            f"{body}",
            status,
        )
    )
    report.add(
        Result(
            "Redis Connection",
            redis_ok or body.get("status") == "ready",
            f"redis={redis_ok} full={body.get('status')}",
            status,
        )
    )

    # 3. Public catalog
    status, body, _ = request(
        "GET", f"{api}/cities", timeout=args.timeout, insecure=insecure
    )
    report.add(
        Result(
            "Tables / Public Catalog (cities)",
            status == 200,
            str(body)[:300],
            status,
        )
    )

    status, body, _ = request(
        "GET",
        f"{api}/home/nearby?lat=28.6139&lng=77.2090&limit=3",
        timeout=args.timeout,
        insecure=insecure,
    )
    parlor_count = len(body) if isinstance(body, list) else (
        len(body.get("items") or body.get("parlors") or []) if isinstance(body, dict) else 0
    )
    report.add(
        Result(
            "Home Nearby Parlors",
            status == 200,
            f"count~{parlor_count} sample={str(body)[:200]}",
            status,
        )
    )

    # 4. Auth — password (admin)
    status, body, _ = request(
        "POST",
        f"{api}/auth/login",
        body={"username": args.admin_user, "password": args.admin_pass},
        timeout=args.timeout,
        insecure=insecure,
    )
    admin_token = body.get("access_token") if isinstance(body, dict) else None
    report.add(
        Result(
            "Auth Admin Login",
            status == 200 and bool(admin_token),
            f"role={((body.get('user') or {}).get('role') if isinstance(body, dict) else None)} msg={str(body)[:200]}",
            status,
        )
    )

    # 5. Auth — user by phone password
    status, body, _ = request(
        "POST",
        f"{api}/auth/login",
        body={"username": args.user_phone, "password": args.user_pass},
        timeout=args.timeout,
        insecure=insecure,
    )
    user_token = body.get("access_token") if isinstance(body, dict) else None
    if not user_token:
        status2, body2, _ = request(
            "POST",
            f"{api}/auth/login",
            body={"username": args.user_username, "password": args.user_pass},
            timeout=args.timeout,
            insecure=insecure,
        )
        user_token = body2.get("access_token") if isinstance(body2, dict) else None
        status, body = status2, body2
    report.add(
        Result(
            "Auth User Login (phone/username)",
            status == 200 and bool(user_token),
            str(body)[:250],
            status,
        )
    )

    # 6. Protected route
    status, body, _ = request(
        "GET",
        f"{api}/auth/me",
        token=user_token or "invalid",
        timeout=args.timeout,
        insecure=insecure,
    )
    report.add(
        Result(
            "Protected /auth/me",
            status == 200 if user_token else status == 401,
            str(body)[:200],
            status,
        )
    )

    # 7. Invalid token rejected
    status, body, _ = request(
        "GET",
        f"{api}/auth/me",
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.sig",
        timeout=args.timeout,
        insecure=insecure,
    )
    report.add(
        Result(
            "Invalid Token Rejected",
            status in (401, 403),
            str(body)[:200],
            status,
        )
    )

    # 8. Admin parlors list
    if admin_token:
        status, body, _ = request(
            "GET",
            f"{api}/admin/parlors?page=1&limit=5",
            token=admin_token,
            timeout=args.timeout,
            insecure=insecure,
        )
        total = body.get("total") if isinstance(body, dict) else None
        report.add(
            Result(
                "Admin Parlor List",
                status == 200,
                f"total={total} sample={str(body)[:200]}",
                status,
            )
        )

        status, body, _ = request(
            "GET",
            f"{api}/admin/stats",
            token=admin_token,
            timeout=args.timeout,
            insecure=insecure,
        )
        report.add(
            Result(
                "Admin Stats",
                status == 200 and isinstance(body, dict) and "users" in body,
                str(body)[:250],
                status,
            )
        )

        # Non-admin must not access admin
        if user_token:
            status, body, _ = request(
                "GET",
                f"{api}/admin/stats",
                token=user_token,
                timeout=args.timeout,
                insecure=insecure,
            )
            report.add(
                Result(
                    "RBAC Admin Guard (user blocked)",
                    status == 403,
                    str(body)[:200],
                    status,
                )
            )
    else:
        report.add(Result("Admin Parlor List", False, "skipped — no admin token"))
        report.add(Result("Admin Stats", False, "skipped — no admin token"))

    # 9. CORS preflight-ish (Origin echo on GET)
    status, body, headers = request(
        "GET",
        f"{base}/health",
        timeout=args.timeout,
        insecure=insecure,
        origin="http://localhost:4200",
    )
    acao = headers.get("Access-Control-Allow-Origin") or headers.get(
        "access-control-allow-origin"
    )
    report.add(
        Result(
            "CORS (Origin localhost:4200)",
            status == 200 and (acao in ("*", "http://localhost:4200") or acao is not None),
            f"ACA-Origin={acao}",
            status,
        )
    )

    # 10. OTP request (may fail without Twilio — report status, not hard-fail if 503/config)
    status, body, _ = request(
        "POST",
        f"{api}/auth/login/request-otp",
        body={"phone_number": args.user_phone},
        timeout=args.timeout,
        insecure=insecure,
    )
    otp_ok = status in (200, 429)  # 429 rate limit still means route works
    # 400/422/500 if Twilio missing is still useful signal
    report.add(
        Result(
            "Auth OTP Request Route",
            otp_ok or status in (200, 400, 422, 503),
            f"(Twilio required in prod for real OTP) {str(body)[:250]}",
            status,
        )
    )

    print("\n=== SUMMARY ===")
    fails = [r for r in report.results if not r.ok]
    print(f"Passed: {len(report.results) - len(fails)} / {len(report.results)}")
    if fails:
        print("Failed checks:")
        for r in fails:
            print(f"  - {r.name}: {r.detail}")
        return 1
    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
