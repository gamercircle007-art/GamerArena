"""Messaging business logic."""

from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.common.social_notify import notify_user
from app.domains.friend.service import FriendService
from app.domains.messaging.models import Message
from app.domains.messaging.repository import MessagingRepository
from app.domains.messaging.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    ParticipantSummary,
)
from app.domains.online.service import OnlineStatusService
from app.domains.user.repository import UserRepository
from app.ws.events import publish_event, publish_to_user


class MessagingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MessagingRepository(session)
        self.user_repo = UserRepository(session)
        self.friend_service = FriendService(session)

    async def _build_conversation_response(
        self,
        conv_id: UUID,
        user_id: UUID,
        redis: aioredis.Redis | None,
    ) -> ConversationResponse:
        conv = await self.repo.get_conversation(conv_id)
        if conv is None:
            raise NotFoundError("Conversation not found")

        participants_data = await self.repo.get_conversation_participants(conv_id)
        online_svc = OnlineStatusService(self.session)
        participants: list[ParticipantSummary] = []
        for user, _part in participants_data:
            is_online = await online_svc.is_user_online(user.id, redis) if redis else False
            participants.append(
                ParticipantSummary(
                    id=user.id,
                    full_name=user.full_name,
                    username=user.username,
                    avatar_url=user.avatar_url,
                    is_online=is_online,
                )
            )

        my_part = await self.repo.get_participant(conv_id, user_id)
        unread = await self.repo.count_unread(conv_id, user_id, my_part.last_read_at if my_part else None)
        preview = await self.repo.get_last_message_preview(conv_id)

        return ConversationResponse(
            id=conv.id,
            type=conv.type,
            is_ephemeral=conv.is_ephemeral,
            theme=conv.theme,
            emoji=conv.emoji,
            last_message_at=conv.last_message_at,
            last_message_preview=preview,
            unread_count=unread,
            participants=participants,
            created_at=conv.created_at,
        )

    async def list_conversations(
        self, user_id: UUID, redis: aioredis.Redis | None
    ) -> list[ConversationResponse]:
        convs = await self.repo.list_user_conversations(user_id)
        return [await self._build_conversation_response(c.id, user_id, redis) for c in convs]

    async def get_conversation(
        self, conversation_id: UUID, user_id: UUID, redis: aioredis.Redis | None
    ) -> ConversationResponse:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        return await self._build_conversation_response(conversation_id, user_id, redis)

    async def create_conversation(
        self, user_id: UUID, data: ConversationCreate
    ) -> ConversationResponse:
        all_ids = list({user_id, *data.participant_ids})
        if data.type == "direct" and len(all_ids) != 2:
            raise ValidationError("Direct conversations require exactly 2 participants")

        if data.type == "direct":
            existing = await self.repo.find_direct_conversation(all_ids[0], all_ids[1])
            if existing:
                return await self._build_conversation_response(existing.id, user_id, None)

        conv = await self.repo.create_conversation(
            conv_type=data.type,
            participant_ids=all_ids,
            is_ephemeral=data.is_ephemeral,
        )
        await self.session.commit()
        return await self._build_conversation_response(conv.id, user_id, None)

    async def find_or_create_dm(self, user_id: UUID, other_user_id: UUID) -> ConversationResponse:
        if user_id == other_user_id:
            raise ValidationError("Cannot message yourself")
        if await self.friend_service.is_blocked(user_id, other_user_id):
            raise ValidationError("Cannot message this user")

        existing = await self.repo.find_direct_conversation(user_id, other_user_id)
        if existing:
            return await self._build_conversation_response(existing.id, user_id, None)

        conv = await self.repo.create_conversation(
            conv_type="direct",
            participant_ids=[user_id, other_user_id],
        )
        await self.session.commit()
        return await self._build_conversation_response(conv.id, user_id, None)

    async def _message_to_response(self, msg: Message) -> MessageResponse:
        sender = await self.user_repo.get_by_id(msg.sender_id)
        return MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            sender_name=sender.full_name if sender else None,
            sender_avatar=sender.avatar_url if sender else None,
            content=msg.content,
            message_type=msg.message_type,
            media_url=msg.media_url,
            thumbnail_url=msg.thumbnail_url,
            duration_seconds=msg.duration_seconds,
            is_ephemeral=msg.is_ephemeral,
            ephemeral_duration=msg.ephemeral_duration,
            viewed_at=msg.viewed_at,
            reply_to_id=msg.reply_to_id,
            location_lat=msg.location_lat,
            location_lng=msg.location_lng,
            sticker_id=msg.sticker_id,
            reactions=msg.reactions or {},
            is_deleted=msg.is_deleted,
            created_at=msg.created_at,
        )

    async def list_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        limit: int = 30,
        before_id: UUID | None = None,
    ) -> list[MessageResponse]:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        messages = await self.repo.get_messages(conversation_id, limit=limit, before_id=before_id)
        return [await self._message_to_response(m) for m in messages]

    async def send_message(
        self,
        conversation_id: UUID,
        sender_id: UUID,
        data: MessageCreate,
        redis: aioredis.Redis,
    ) -> MessageResponse:
        part = await self.repo.get_participant(conversation_id, sender_id)
        if part is None:
            raise NotFoundError("Conversation not found")

        if not data.content and not data.media_url and data.message_type == "text":
            raise ValidationError("Message content required")

        conv = await self.repo.get_conversation(conversation_id)
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=data.content,
            message_type=data.message_type,
            media_url=data.media_url,
            thumbnail_url=data.thumbnail_url,
            duration_seconds=data.duration_seconds,
            is_ephemeral=data.is_ephemeral or (conv.is_ephemeral if conv else False),
            ephemeral_duration=data.ephemeral_duration,
            reply_to_id=data.reply_to_id,
            location_lat=data.location_lat,
            location_lng=data.location_lng,
            sticker_id=data.sticker_id,
            reactions={},
        )
        created = await self.repo.create_message(msg)
        now = datetime.now(timezone.utc)
        await self.repo.update_conversation_last_message(conversation_id, now)
        await self.session.commit()

        response = await self._message_to_response(created)
        ws_payload = {
            "type": "new_message",
            "conversation_id": str(conversation_id),
            "message": response.model_dump(mode="json"),
        }
        await publish_event(redis, f"conversation:{conversation_id}", "new_message", ws_payload)

        participants = await self.repo.get_conversation_participants(conversation_id)
        for user, _ in participants:
            if user.id != sender_id:
                await publish_to_user(redis, user.id, ws_payload)
                sender = await self.user_repo.get_by_id(sender_id)
                await notify_user(
                    self.session,
                    redis,
                    user.id,
                    type="new_message",
                    title=sender.full_name if sender else "New message",
                    body=(data.content or "Sent a message")[:120],
                    data={
                        "conversation_id": str(conversation_id),
                        "sender_id": str(sender_id),
                    },
                    skip_if_online=True,
                )

        return response

    async def add_reaction(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
        emoji: str,
        redis: aioredis.Redis,
    ) -> MessageResponse:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        msg = await self.repo.get_message(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            raise NotFoundError("Message not found")

        reactions = dict(msg.reactions or {})
        users = reactions.get(emoji, [])
        uid = str(user_id)
        if uid not in users:
            users.append(uid)
        reactions[emoji] = users
        msg.reactions = reactions
        await self.session.commit()

        response = await self._message_to_response(msg)
        payload = {
            "type": "message_reaction",
            "message_id": str(message_id),
            "user_id": uid,
            "emoji": emoji,
            "action": "add",
        }
        await publish_event(redis, f"conversation:{conversation_id}", "message_reaction", payload)
        return response

    async def remove_reaction(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
        redis: aioredis.Redis,
    ) -> MessageResponse:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        msg = await self.repo.get_message(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            raise NotFoundError("Message not found")

        reactions = dict(msg.reactions or {})
        uid = str(user_id)
        for emoji, users in list(reactions.items()):
            if uid in users:
                users = [u for u in users if u != uid]
                if users:
                    reactions[emoji] = users
                else:
                    del reactions[emoji]
        msg.reactions = reactions
        await self.session.commit()
        return await self._message_to_response(msg)

    async def mark_ephemeral_viewed(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
        redis: aioredis.Redis,
    ) -> MessageResponse:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        msg = await self.repo.get_message(message_id)
        if msg is None or not msg.is_ephemeral:
            raise NotFoundError("Message not found")

        if msg.viewed_at is None:
            msg.viewed_at = datetime.now(timezone.utc)
            await self.session.commit()
            payload = {
                "type": "ephemeral_viewed",
                "message_id": str(message_id),
                "delete_in_seconds": msg.ephemeral_duration,
            }
            await publish_event(redis, f"conversation:{conversation_id}", "ephemeral_viewed", payload)
            try:
                from app.tasks.ephemeral_messages import delete_ephemeral_message

                delete_ephemeral_message.apply_async(
                    args=[str(message_id)],
                    countdown=msg.ephemeral_duration,
                )
            except Exception:
                pass

        return await self._message_to_response(msg)

    async def mark_message_delivered(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
        redis: aioredis.Redis,
    ) -> None:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            return
        msg = await self.repo.get_message(message_id)
        if msg is None or msg.sender_id == user_id:
            return
        payload = {
            "type": "message_delivered",
            "message_id": str(message_id),
            "conversation_id": str(conversation_id),
            "recipient_id": str(user_id),
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }
        await publish_event(redis, f"conversation:{conversation_id}", "message_delivered", payload)

    async def delete_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
        redis: aioredis.Redis,
    ) -> None:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        msg = await self.repo.get_message(message_id)
        if msg is None or msg.sender_id != user_id:
            raise NotFoundError("Message not found")
        msg.is_deleted = True
        await self.session.commit()
        payload = {"type": "message_deleted", "message_id": str(message_id)}
        await publish_event(redis, f"conversation:{conversation_id}", "message_deleted", payload)

    async def mark_read(
        self,
        conversation_id: UUID,
        user_id: UUID,
        last_message_id: UUID | None,
        redis: aioredis.Redis,
    ) -> None:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            return
        await self.repo.mark_read(conversation_id, user_id)
        await self.session.commit()
        if last_message_id:
            payload = {
                "type": "message_read",
                "message_id": str(last_message_id),
                "conversation_id": str(conversation_id),
                "reader_id": str(user_id),
                "read_at": datetime.now(timezone.utc).isoformat(),
            }
            await publish_event(redis, f"conversation:{conversation_id}", "message_read", payload)

    async def list_media(
        self, conversation_id: UUID, user_id: UUID
    ) -> list[MessageResponse]:
        part = await self.repo.get_participant(conversation_id, user_id)
        if part is None:
            raise NotFoundError("Conversation not found")
        messages = await self.repo.get_media_messages(conversation_id)
        return [await self._message_to_response(m) for m in messages]