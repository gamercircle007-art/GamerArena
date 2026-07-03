"""Messaging data access."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domains.messaging.models import Conversation, ConversationParticipant, Message
from app.domains.user.models import User


class MessagingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_participant(
        self, conversation_id: UUID, user_id: UUID
    ) -> ConversationParticipant | None:
        result = await self.session.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_user_conversations(self, user_id: UUID) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .join(ConversationParticipant)
            .where(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_conversation_participants(self, conversation_id: UUID) -> list[tuple[User, ConversationParticipant]]:
        result = await self.session.execute(
            select(User, ConversationParticipant)
            .join(ConversationParticipant, ConversationParticipant.user_id == User.id)
            .where(ConversationParticipant.conversation_id == conversation_id)
        )
        return list(result.all())

    async def find_direct_conversation(self, user1: UUID, user2: UUID) -> Conversation | None:
        cp1 = aliased(ConversationParticipant)
        cp2 = aliased(ConversationParticipant)
        result = await self.session.execute(
            select(Conversation)
            .join(cp1, cp1.conversation_id == Conversation.id)
            .join(cp2, cp2.conversation_id == Conversation.id)
            .where(
                Conversation.type == "direct",
                cp1.user_id == user1,
                cp2.user_id == user2,
            )
        )
        return result.scalar_one_or_none()

    async def create_conversation(
        self,
        *,
        conv_type: str,
        participant_ids: list[UUID],
        is_ephemeral: bool = False,
    ) -> Conversation:
        conv = Conversation(type=conv_type, is_ephemeral=is_ephemeral)
        self.session.add(conv)
        await self.session.flush()
        for uid in participant_ids:
            self.session.add(
                ConversationParticipant(conversation_id=conv.id, user_id=uid)
            )
        await self.session.flush()
        return conv

    async def get_messages(
        self,
        conversation_id: UUID,
        *,
        limit: int = 30,
        before_id: UUID | None = None,
    ) -> list[Message]:
        query = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.is_deleted.is_(False),
        )
        if before_id:
            before_msg = await self.session.get(Message, before_id)
            if before_msg:
                query = query.where(Message.created_at < before_msg.created_at)
        query = query.order_by(Message.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_message(self, message_id: UUID) -> Message | None:
        return await self.session.get(Message, message_id)

    async def create_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def update_conversation_last_message(self, conversation_id: UUID, at: datetime) -> None:
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(last_message_at=at)
        )

    async def count_unread(
        self, conversation_id: UUID, user_id: UUID, last_read_at: datetime | None
    ) -> int:
        query = select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.is_deleted.is_(False),
        )
        if last_read_at:
            query = query.where(Message.created_at > last_read_at)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def get_last_message_preview(self, conversation_id: UUID) -> str | None:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.is_deleted.is_(False))
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        msg = result.scalar_one_or_none()
        if not msg:
            return None
        if msg.is_ephemeral:
            return "🔥 Ephemeral message"
        if msg.message_type != "text":
            return f"{msg.message_type.capitalize()} message"
        return (msg.content or "")[:100]

    async def mark_read(self, conversation_id: UUID, user_id: UUID) -> None:
        await self.session.execute(
            update(ConversationParticipant)
            .where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
            .values(last_read_at=datetime.now(timezone.utc))
        )

    async def get_media_messages(self, conversation_id: UUID) -> list[Message]:
        result = await self.session.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.is_deleted.is_(False),
                Message.message_type.in_(["image", "video", "audio"]),
            ).order_by(Message.created_at.desc())
        )
        return list(result.scalars().all())