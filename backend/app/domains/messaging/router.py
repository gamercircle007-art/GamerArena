"""Messaging API routes."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.messaging.schemas import (
    ConversationCreate,
    ConversationResponse,
    FindOrCreateConversation,
    MessageCreate,
    MessageResponse,
    ReactionCreate,
)
from app.domains.messaging.service import MessagingService

router = APIRouter(prefix="/conversations", tags=["Messaging"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    return await MessagingService(db).create_conversation(current_user.id, body)


@router.post("/find-or-create", response_model=ConversationResponse)
async def find_or_create_conversation(
    body: FindOrCreateConversation,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    return await MessagingService(db).find_or_create_dm(current_user.id, body.user_id)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> list[ConversationResponse]:
    return await MessagingService(db).list_conversations(current_user.id, redis)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> ConversationResponse:
    return await MessagingService(db).get_conversation(conversation_id, current_user.id, redis)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    limit: int = Query(default=30, ge=1, le=100),
    before_id: UUID | None = None,
) -> list[MessageResponse]:
    return await MessagingService(db).list_messages(
        conversation_id, current_user.id, limit=limit, before_id=before_id
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID,
    body: MessageCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    return await MessagingService(db).send_message(
        conversation_id, current_user.id, body, redis
    )


@router.post("/{conversation_id}/messages/{message_id}/react", response_model=MessageResponse)
async def add_reaction(
    conversation_id: UUID,
    message_id: UUID,
    body: ReactionCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    return await MessagingService(db).add_reaction(
        conversation_id, message_id, current_user.id, body.emoji, redis
    )


@router.delete("/{conversation_id}/messages/{message_id}/react", response_model=MessageResponse)
async def remove_reaction(
    conversation_id: UUID,
    message_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    return await MessagingService(db).remove_reaction(
        conversation_id, message_id, current_user.id, redis
    )


@router.put("/{conversation_id}/messages/{message_id}/delivered", status_code=status.HTTP_204_NO_CONTENT)
async def mark_message_delivered(
    conversation_id: UUID,
    message_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> None:
    await MessagingService(db).mark_message_delivered(
        conversation_id, message_id, current_user.id, redis
    )


@router.put("/{conversation_id}/messages/{message_id}/viewed", response_model=MessageResponse)
async def mark_ephemeral_viewed(
    conversation_id: UUID,
    message_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> MessageResponse:
    return await MessagingService(db).mark_ephemeral_viewed(
        conversation_id, message_id, current_user.id, redis
    )


@router.delete("/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    conversation_id: UUID,
    message_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> None:
    await MessagingService(db).delete_message(
        conversation_id, message_id, current_user.id, redis
    )


@router.get("/{conversation_id}/media", response_model=list[MessageResponse])
async def list_media(
    conversation_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[MessageResponse]:
    return await MessagingService(db).list_media(conversation_id, current_user.id)