"""Redis pub/sub helpers for WebSocket fan-out."""

import json
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis


async def publish_event(redis: aioredis.Redis, channel: str, event: str, payload: dict[str, Any]) -> None:
    message = json.dumps({"event": event, "channel": channel, "payload": payload, **payload})
    await redis.publish(f"ws:{channel}", message)


async def publish_to_user(redis: aioredis.Redis, user_id: UUID, payload: dict[str, Any]) -> None:
    """Deliver an event to a user's personal WS channel."""
    channel = f"user:{user_id}"
    event = payload.get("type", "notification")
    await publish_event(redis, channel, event, payload)