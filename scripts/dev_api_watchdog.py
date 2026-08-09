#!/usr/bin/env python3
"""Dev API watchdog — probe live endpoints and refresh the error backlog.

Run locally or via GitHub Actions every 25 minutes:
  python scripts/dev_api_watchdog.py
  python scripts/dev_api_watchdog.py --base https://gamer-circle-api.onrender.com

Exit code 1 if any FAIL remains (CI can open/keep a failing check).
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "DEV_ERROR_BACKLOG.md"
REPORT_JSON = ROOT / "docs" / "dev_watchdog_report.json"

# Public probes: 200 expected (or documented soft status).
# Auth probes: 401/403/422 = healthy without a token; 404/405/500 = broken.
CHECKS: list[tuple[str, str, str, dict | None]] = [
    # kind, method, path, body
    ("public", "GET", "/health", None),
    ("public", "GET", "/api/v1/home", None),
    ("public", "GET", "/api/v1/feed/ranked", None),
    ("public", "GET", "/api/v1/reels/feed?page=1&limit=1", None),
    ("public", "GET", "/api/v1/geo/nearby-parlors?lat=28.6139&lng=77.209&radius_km=30", None),
    ("public", "GET", "/api/v1/search?q=vr&limit=5", None),
    ("public", "GET", "/api/v1/search/smart?q=vr&limit=5", None),
    ("public", "GET", "/api/v1/discovery/centres?lat=28.6139&lng=77.209&radius_km=20", None),
    (
        "public",
        "GET",
        "/api/v1/parlors/316a4e1c-2882-4ee1-87f6-e007e042798d/availability?date=2026-08-10&station_type=PC",
        None,
    ),
    (
        "public",
        "GET",
        "/api/v1/clubs/316a4e1c-2882-4ee1-87f6-e007e042798d/availability?date=2026-08-10&station_type=PC",
        None,
    ),
    ("auth", "POST", "/api/v1/bookings/hold", {}),
    ("auth", "POST", "/api/v1/bookings/v2", {}),
    ("auth", "GET", "/api/v1/conversations", None),
    ("auth", "GET", "/api/v1/feed", None),
    ("auth", "POST", "/api/v1/posts", {"content": "watchdog"}),
]


def _request(base: str, method: str, path: str, body: dict | None) -> tuple[int, str]:
    url = base.rstrip("/") + path
    data = None
    headers = {"Accept": "application/json", "User-Agent": "gamer-circle-watchdog/1.0"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()[:400]
            return resp.status, raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read()[:400]
        return exc.code, raw.decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def _classify(kind: str, path: str, code: int) -> str:
    if path.endswith("/health") or path == "/health":
        return "OK" if code == 200 else "FAIL"
    if kind == "public":
        if code == 200:
            return "OK"
        # Soft-empty discovery while undeployed still FAIL so we notice
        return "FAIL"
    # auth
    if code in (200, 201, 401, 403, 422):
        return "AUTH_OK"
    return "FAIL"


def _msg(raw: str) -> str:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return str(
                data.get("detail")
                or data.get("message")
                or data.get("error")
                or data.get("version")
                or list(data.keys())[:4]
            )[:160]
        return str(data)[:160]
    except Exception:  # noqa: BLE001
        return raw[:160]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        default="https://gamer-circle-api.onrender.com",
        help="API origin (no /api/v1 suffix for /health)",
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows: list[dict] = []
    for kind, method, path, body in CHECKS:
        # /health is on origin root
        probe_path = "/health" if path.endswith("/health") and path.count("/") <= 1 else path
        if path == "/health":
            probe_path = "/health"
        code, raw = _request(base, method, probe_path if path == "/health" else path, body)
        status = _classify(kind, path, code)
        rows.append(
            {
                "status": status,
                "kind": kind,
                "method": method,
                "path": path,
                "code": code,
                "message": _msg(raw),
            }
        )

    fails = [r for r in rows if r["status"] == "FAIL"]
    auth_ok = [r for r in rows if r["status"] == "AUTH_OK"]
    oks = [r for r in rows if r["status"] == "OK"]

    health = next((r for r in rows if r["path"] == "/health"), None)
    api_version = health["message"] if health else "?"

    lines = [
        "# Dev error backlog (auto-refreshed)",
        "",
        f"Last probe: **{now}**  ",
        f"Target: `{base}`  ",
        f"Health version field: `{api_version}`  ",
        f"Summary: **{len(fails)} FAIL** · {len(oks)} OK · {len(auth_ok)} auth-gated",
        "",
        "## Open failures (fix these)",
        "",
    ]
    if not fails:
        lines.append("_None — all probed routes healthy for this environment._")
    else:
        lines.append("| # | Code | Method | Path | Message | Likely fix |")
        lines.append("|---|------|--------|------|---------|------------|")
        for i, r in enumerate(fails, 1):
            hint = _hint(r)
            lines.append(
                f"| {i} | {r['code']} | `{r['method']}` | `{r['path']}` | {r['message'][:80]} | {hint} |"
            )

    lines += [
        "",
        "## Known root causes (checklist)",
        "",
        "1. **[P0] Render API stuck on old deploy** — `/health` version not matching `sit`. "
        "Dashboard → gamer-circle-api → Manual Deploy → Clear build cache (branch `sit`).",
        "2. **[P0] Flutter path aliases** — use `/parlors/{id}/availability` (not `/clubs/...`); "
        "`ApiCompatInterceptor` strips double `/api/v1`.",
        "3. **[P1] `/reels/feed` 500** — soft-fail empty feed if DB schema missing (deploy required).",
        "4. **[P1] `/search/smart` 404** — alias added; Flutter falls back to `/search`.",
        "5. **[P1] `/bookings/hold` 405** — missing on old deploy; after redeploy should return 401/422.",
        "6. **[P1] `/discovery/centres` 404** — missing on old deploy; ships with `sit`.",
        "",
        "## Auth-gated (OK without token)",
        "",
    ]
    for r in auth_ok:
        lines.append(f"- `{r['code']}` `{r['method']}` `{r['path']}`")

    lines += ["", "## Passing public probes", ""]
    for r in oks:
        lines.append(f"- `{r['code']}` `{r['method']}` `{r['path']}`")
    lines.append("")

    BACKLOG.parent.mkdir(parents=True, exist_ok=True)
    BACKLOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    REPORT_JSON.write_text(
        json.dumps({"probed_at": now, "base": base, "results": rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {BACKLOG.relative_to(ROOT)} ({len(fails)} FAIL)")
    for r in fails:
        print(f"  FAIL [{r['code']}] {r['method']} {r['path']} :: {r['message'][:100]}")
    return 1 if fails else 0


def _hint(row: dict) -> str:
    path = row["path"]
    code = row["code"]
    if "discovery" in path and code == 404:
        return "Redeploy sit (discovery router missing on live)"
    if "/clubs/" in path and code == 404:
        return "Redeploy sit OR client uses /parlors (compat interceptor)"
    if path.endswith("/bookings/hold") and code == 405:
        return "Redeploy sit — hold route not mounted; shadowed by GET /bookings/{id}"
    if "/reels/feed" in path and code == 500:
        return "Deploy soft-fail feed; run alembic for reels tables"
    if "/search/smart" in path and code == 404:
        return "Deploy /search/smart alias; app falls back to /search"
    if code == 0:
        return "Network / cold start — retry"
    return "Investigate response + recent sit deploy"


if __name__ == "__main__":
    sys.exit(main())
