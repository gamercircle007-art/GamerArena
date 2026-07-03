"""Follow domain Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel


class FollowCreate(BaseModel):
    parlor_id: UUID