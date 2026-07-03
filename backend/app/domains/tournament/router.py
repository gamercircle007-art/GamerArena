"""
Tournament domain API routes.

| Method | Endpoint              | Auth   | Description              |
|--------|-----------------------|--------|--------------------------|
| POST   | /tournaments          | Owner  | Create tournament        |
| GET    | /tournaments/{id}     | Public | Tournament detail        |
| PUT    | /tournaments/{id}     | Owner  | Update tournament        |
| DELETE | /tournaments/{id}     | Owner  | Delete tournament        |
"""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep, RedisDep, RedisDep
from app.domains.tournament.schemas import TournamentCreate, TournamentResponse, TournamentUpdate
from app.domains.tournament.service import TournamentService

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


@router.post(
    "",
    response_model=TournamentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tournament",
    description="Parlor owners only. Tournament is created for the owner's parlor.",
)
async def create_tournament(
    body: TournamentCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> TournamentResponse:
    service = TournamentService(db)
    return await service.create_tournament(
        current_user.id,
        body,
        user_role=current_user.role.value,
    )


@router.get(
    "/{tournament_id}",
    response_model=TournamentResponse,
    summary="Get tournament by ID",
)
async def get_tournament(
    tournament_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: OptionalCurrentUserDep = None,
) -> TournamentResponse:
    viewer_id = current_user.id if current_user else None
    service = TournamentService(db)
    return await service.get_tournament(tournament_id, viewer_id, redis=redis)


@router.put(
    "/{tournament_id}",
    response_model=TournamentResponse,
    summary="Update a tournament",
)
async def update_tournament(
    tournament_id: UUID,
    body: TournamentUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> TournamentResponse:
    service = TournamentService(db)
    return await service.update_tournament(tournament_id, current_user.id, body)


@router.delete(
    "/{tournament_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tournament",
)
async def delete_tournament(
    tournament_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    service = TournamentService(db)
    await service.delete_tournament(tournament_id, current_user.id)