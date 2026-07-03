"""Stories API routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.story.schemas import StoryCreate, StoryGroupResponse, StoryResponse, StoryViewerResponse
from app.domains.story.service import StoryService

router = APIRouter(prefix="/stories", tags=["Stories"])


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    body: StoryCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> StoryResponse:
    return await StoryService(db).create_story(current_user.id, body, redis)


@router.get("/feed", response_model=list[StoryGroupResponse])
async def stories_feed(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[StoryGroupResponse]:
    return await StoryService(db).get_feed(current_user.id)


@router.get("/user/{user_id}", response_model=list[StoryResponse])
async def user_stories(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[StoryResponse]:
    return await StoryService(db).get_user_stories(user_id, current_user.id)


@router.post("/{story_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def mark_viewed(
    story_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await StoryService(db).mark_viewed(story_id, current_user.id)


@router.get("/{story_id}/viewers", response_model=list[StoryViewerResponse])
async def story_viewers(
    story_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[StoryViewerResponse]:
    return await StoryService(db).get_viewers(story_id, current_user.id)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await StoryService(db).delete_story(story_id, current_user.id)