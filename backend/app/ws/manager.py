"""WebSocket connection manager with Redis pub/sub bridge."""

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._subscriptions: dict[UUID, set[str]] = defaultdict(set)
        self._channel_index: dict[str, set[UUID]] = defaultdict(set)
        self._listener_task: asyncio.Task[None] | None = None

    async def connect(self, websocket: WebSocket, user_id: UUID) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if conns and websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)
            for channel in list(self._subscriptions.get(user_id, set())):
                self._channel_index[channel].discard(user_id)
            self._subscriptions.pop(user_id, None)

    def subscribe(self, user_id: UUID, channel: str) -> None:
        self._subscriptions[user_id].add(channel)
        self._channel_index[channel].add(user_id)

    def unsubscribe(self, user_id: UUID, channel: str) -> None:
        subs = self._subscriptions.get(user_id)
        if subs and channel in subs:
            subs.remove(channel)
        users = self._channel_index.get(channel)
        if users:
            users.discard(user_id)

    async def send_to_user(self, user_id: UUID, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(user_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast_to_channel(self, channel: str, message: dict[str, Any]) -> None:
        for user_id in list(self._channel_index.get(channel, set())):
            await self.send_to_user(user_id, message)

    async def start_redis_listener(self, redis: aioredis.Redis) -> None:
        if self._listener_task and not self._listener_task.done():
            return

        async def _listen() -> None:
            pubsub = redis.pubsub()
            await pubsub.psubscribe("ws:*")
            async for raw in pubsub.listen():
                if raw["type"] not in {"pmessage", "message"}:
                    continue
                data = raw.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                if not isinstance(data, str):
                    continue
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    continue
                channel = payload.get("channel")
                if channel:
                    await self.broadcast_to_channel(channel, payload)

        self._listener_task = asyncio.create_task(_listen())

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()


ws_manager = ConnectionManager()