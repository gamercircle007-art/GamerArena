"""Tournament group chat WebSocket channel scaffold (Phase 3)."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUserDep, RedisDep
from app.ws.events import publish_event

router = APIRouter(prefix="/tournaments", tags=["Tournament Chat"])


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    tournament_id: UUID
    user_id: UUID
    content: str
    status: str


@router.post("/{tournament_id}/chat", response_model=ChatMessageResponse)
async def send_tournament_chat_message(
    tournament_id: UUID,
    body: ChatMessageCreate,
    current_user: CurrentUserDep,
    redis: RedisDep,
) -> ChatMessageResponse:
    """Publish chat message to tournament_chat:{id} WS channel."""
    payload = {
        "tournament_id": str(tournament_id),
        "user_id": str(current_user.id),
        "content": body.content,
    }
    await publish_event(redis, f"tournament_chat:{tournament_id}", "chat_message", payload)
    return ChatMessageResponse(
        tournament_id=tournament_id,
        user_id=current_user.id,
        content=body.content,
        status="published",
    )