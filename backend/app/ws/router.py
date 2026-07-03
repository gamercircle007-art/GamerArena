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