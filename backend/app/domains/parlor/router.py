"""Parlor domain API routes."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep
from app.domains.parlor.schemas import (
    ParlorAnalyticsResponse,
    ParlorCreate,
    ParlorResponse,
    ParlorUpdate,
)
from app.domains.parlor.service import ParlorService
from app.domains.post.schemas import PostResponse
from app.domains.post.service import PostService
from app.domains.tournament.schemas import TournamentResponse
from app.domains.tournament.service import TournamentService

router = APIRouter(prefix="/parlors", tags=["Parlors"])


@router.post("", response_model=ParlorResponse, status_code=status.HTTP_201_CREATED)
async def create_parlor(
    body: ParlorCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ParlorResponse:
    return await ParlorService(db).create_parlor(
        current_user.id,
        body,
        user_role=current_user.role.value,
    )


@router.get("/me/analytics", response_model=ParlorAnalyticsResponse)
async def get_my_parlor_analytics(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ParlorAnalyticsResponse:
    return await ParlorService(db).get_owner_analytics(current_user.id)


@router.get("/{parlor_id}", response_model=ParlorResponse)
async def get_parlor(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: OptionalCurrentUserDep = None,
) -> ParlorResponse:
    viewer_id = current_user.id if current_user else None
    return await ParlorService(db).get_parlor(parlor_id, viewer_id)


@router.put("/{parlor_id}", response_model=ParlorResponse)
async def update_parlor(
    parlor_id: UUID,
    body: ParlorUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ParlorResponse:
    return await ParlorService(db).update_parlor(parlor_id, current_user.id, body)


@router.get("/{parlor_id}/posts", response_model=list[PostResponse])
async def list_parlor_posts(
    parlor_id: UUID,
    db: DbSessionDep,
    limit: int = Query(default=20, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    current_user: OptionalCurrentUserDep = None,
) -> list[PostResponse]:
    viewer_id = current_user.id if current_user else None
    offset = (page - 1) * limit
    return await PostService(db).list_parlor_posts(
        parlor_id, limit=limit, offset=offset, viewer_id=viewer_id
    )


@router.get("/{parlor_id}/tournaments", response_model=list[TournamentResponse])
async def list_parlor_tournaments(
    parlor_id: UUID,
    db: DbSessionDep,
    status: str | None = Query(default=None, description="Filter by status, e.g. open"),
    upcoming: bool | None = Query(default=None, description="Only future tournaments"),
    current_user: OptionalCurrentUserDep = None,
) -> list[TournamentResponse]:
    viewer_id = current_user.id if current_user else None
    return await TournamentService(db).list_parlor_tournaments(
        parlor_id,
        status=status,
        upcoming=upcoming,
        viewer_id=viewer_id,
    )