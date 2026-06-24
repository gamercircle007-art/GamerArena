#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for PostgreSQL..."
until python -c "
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def check() -> None:
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__('sqlalchemy').text('SELECT 1'))
    finally:
        await engine.dispose()

asyncio.run(check())
" 2>/dev/null; do
  echo "PostgreSQL not ready — retrying in 2s..."
  sleep 2
done

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"