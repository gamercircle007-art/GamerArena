"""Messaging API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    participant_ids: list[UUID] = Field(min_length=1)
    type: str = "direct"
    is_ephemeral: bool = False


class FindOrCreateConversation(BaseModel):
    user_id: UUID


class MessageCreate(BaseModel):
    content: str | None = None
    message_type: str = "text"
    media_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    reply_to_id: UUID | None = None
    is_ephemeral: bool = False
    ephemeral_duration: int = 10
    location_lat: float | None = None
    location_lng: float | None = None
    sticker_id: str | None = None


class ReactionCreate(BaseModel):
    emoji: str = Field(min_length=1, max_length=10)


class ParticipantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None = Field(validation_alias="full_name")
    username: str | None = None
    avatar_url: str | None = None
    is_online: bool = False


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender_name: str | None = None
    sender_avatar: str | None = None
    content: str | None = None
    message_type: str
    media_url: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    is_ephemeral: bool
    ephemeral_duration: int
    viewed_at: datetime | None = None
    reply_to_id: UUID | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    sticker_id: str | None = None
    reactions: dict = Field(default_factory=dict)
    is_deleted: bool = False
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    is_ephemeral: bool
    theme: str
    emoji: str | None = None
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    unread_count: int = 0
    participants: list[ParticipantSummary] = Field(default_factory=list)
    created_at: datetime