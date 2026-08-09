"""WebSocket endpoint."""

import json
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.db.session import get_session_factory
from app.domains.messaging.service import MessagingService
from app.domains.online.service import OnlineStatusService
from app.ws.events import publish_event
from app.ws.manager import ws_manager

router = APIRouter(tags=["WebSocket"])

TYPING_TTL = 5
TYPING_KEY = "typing:{}:{}"


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    settings = get_settings()
    payload = decode_token(token, settings)
    if payload is None or payload.token_type != TOKEN_TYPE_ACCESS:
        await websocket.close(code=4401)
        return

    user_id = UUID(payload.sub)

    import redis.asyncio as aioredis

    redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    await ws_manager.connect(websocket, user_id)

    factory = get_session_factory()
    async with factory() as session:
        online_svc = OnlineStatusService(session)
        await online_svc.set_user_online(user_id, redis)

    await websocket.send_json({
        "type": "connected",
        "user_id": str(user_id),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            if raw == "ping":
                await websocket.send_text("pong")
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get("action") or msg.get("type")

            if action == "heartbeat":
                async with factory() as session:
                    await OnlineStatusService(session).heartbeat(user_id, redis)
                continue

            if action == "subscribe":
                channel = msg.get("channel")
                if channel and isinstance(channel, str):
                    ws_manager.subscribe(user_id, channel)
                continue

            if action == "unsubscribe":
                channel = msg.get("channel")
                if channel and isinstance(channel, str):
                    ws_manager.unsubscribe(user_id, channel)
                continue

            conversation_id = msg.get("conversation_id")
            if action == "typing_start" and conversation_id:
                await redis.setex(TYPING_KEY.format(conversation_id, user_id), TYPING_TTL, "1")
                await publish_event(
                    redis,
                    f"conversation:{conversation_id}",
                    "typing_start",
                    {
                        "type": "typing_start",
                        "conversation_id": conversation_id,
                        "user_id": str(user_id),
                    },
                )
                continue

            if action == "typing_stop" and conversation_id:
                await redis.delete(TYPING_KEY.format(conversation_id, user_id))
                await publish_event(
                    redis,
                    f"conversation:{conversation_id}",
                    "typing_stop",
                    {
                        "type": "typing_stop",
                        "conversation_id": conversation_id,
                        "user_id": str(user_id),
                    },
                )
                continue

            if action == "mark_read" and conversation_id:
                last_message_id = msg.get("last_message_id")
                async with factory() as session:
                    svc = MessagingService(session)
                    await svc.mark_read(
                        UUID(conversation_id),
                        user_id,
                        UUID(last_message_id) if last_message_id else None,
                        redis,
                    )
                continue

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(user_id, websocket)
        async with factory() as session:
            await OnlineStatusService(session).set_user_offline(user_id, redis)
        await redis.aclose()

@router.websocket("/api/v1/ws/clubs/{club_id}/availability")
async def club_availability_ws(
    websocket: WebSocket,
    club_id: UUID,
    token: str = Query(...),
) -> None:
    """Realtime slot deltas for one club. Deltas only — never full grid.

    Client sends last `v` on connect/reconnect; if server cannot replay → {"t":"resync"}.
    Heartbeat: client ping every 30s; drop dead sockets after ~35s silence.
    """
    import asyncio

    import redis.asyncio as aioredis

    settings = get_settings()
    payload = decode_token(token, settings)
    if payload is None or payload.token_type != TOKEN_TYPE_ACCESS:
        await websocket.close(code=4401)
        return

    user_id = UUID(payload.sub)
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    channel = f"avail:{club_id}"
    await ws_manager.connect(websocket, user_id)  # accepts once
    ws_manager.subscribe(user_id, channel)

    # Also subscribe Redis channel so multi-worker fan-out works via publish_delta
    # (publish_event already uses ws:{channel}; LockService also publishes avail:{id}).
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    async def _relay() -> None:
        async for raw in pubsub.listen():
            if raw["type"] not in {"message", "pmessage"}:
                continue
            data = raw.get("data")
            if isinstance(data, bytes):
                data = data.decode()
            if not isinstance(data, str):
                continue
            try:
                payload_msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            try:
                await websocket.send_json(payload_msg)
            except Exception:  # noqa: BLE001
                break

    relay_task = asyncio.create_task(_relay())
    try:
        current_v = int(await redis.get(f"avail:v:{club_id}") or 0)
        await websocket.send_json({"t": "hello", "v": current_v, "club_id": str(club_id)})

        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=35.0)
            except TimeoutError:
                await websocket.close(code=4408)
                break

            if raw == "ping":
                await websocket.send_text("pong")
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("t") in ("hello", "sync") or msg.get("action") == "sync":
                client_v = int(msg.get("v") or 0)
                server_v = int(await redis.get(f"avail:v:{club_id}") or 0)
                if client_v < server_v:
                    await websocket.send_json({"t": "resync", "v": server_v})
                else:
                    await websocket.send_json({"t": "ok", "v": server_v})
    except WebSocketDisconnect:
        pass
    finally:
        relay_task.cancel()
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:  # noqa: BLE001
            pass
        ws_manager.unsubscribe(user_id, channel)
        ws_manager.disconnect(user_id, websocket)
        await redis.aclose()
