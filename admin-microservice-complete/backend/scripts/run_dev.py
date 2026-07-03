#!/usr/bin/env python3
"""Run the admin microservice on port 8001."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn

from app.config import settings

if __name__ == "__main__":
    print(f"Admin API  → http://localhost:{settings.PORT}")
    print(f"API docs   → http://localhost:{settings.PORT}/docs")
    print(f"Health     → http://localhost:{settings.PORT}/health")
    print("Login      → username: admin  password: Admin@123")
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)