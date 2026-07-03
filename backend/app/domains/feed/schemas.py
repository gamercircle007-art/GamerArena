"""Feed domain Pydantic schemas."""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.domains.post.schemas import PostResponse
from app.domains.tournament.schemas import TournamentResponse


class FeedPostItem(BaseModel):
    type: Literal["post"] = "post"
    data: PostResponse


class FeedTournamentItem(BaseModel):
    type: Literal["tournament_announcement"] = "tournament_announcement"
    data: TournamentResponse


FeedItem = Annotated[
    Union[FeedPostItem, FeedTournamentItem],
    Field(discriminator="type"),
]


class FeedResponse(BaseModel):
    items: list[FeedItem] = Field(default_factory=list)
    page: int
    limit: int