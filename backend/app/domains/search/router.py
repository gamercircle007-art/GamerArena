"""Search domain API routes."""

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.core.dependencies import DbSessionDep
from app.domains.parlor.repository import ParlorRepository
from app.domains.search.schemas import SearchResultItem
from app.domains.tournament.models import Tournament

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=list[SearchResultItem])
async def search(
    db: DbSessionDep,
    q: str = Query(..., min_length=1, max_length=100),
    type: str = Query(default="all", pattern=r"^(all|parlor|tournament)$"),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[SearchResultItem]:
    pattern = f"%{q.strip()}%"
    results: list[SearchResultItem] = []
    per_type = limit if type != "all" else max(limit // 2, 1)

    if type in ("all", "parlor"):
        parlors = await ParlorRepository(db).search(pattern, limit=per_type)
        for parlor in parlors:
            results.append(
                SearchResultItem(
                    type="parlor",
                    data={
                        "id": str(parlor.id),
                        "name": parlor.name,
                        "logo_url": parlor.logo_url,
                        "is_verified": parlor.is_verified,
                        "game_types": parlor.game_types,
                        "rating": parlor.rating,
                    },
                )
            )

    if type in ("all", "tournament"):
        tournament_rows = await db.execute(
            select(Tournament)
            .where(
                or_(
                    Tournament.title.ilike(pattern),
                    Tournament.game_type.ilike(pattern),
                )
            )
            .limit(per_type)
        )
        for tournament in tournament_rows.scalars():
            results.append(
                SearchResultItem(
                    type="tournament",
                    data={
                        "id": str(tournament.id),
                        "parlor_id": str(tournament.parlor_id),
                        "title": tournament.title,
                        "game_type": tournament.game_type,
                        "status": tournament.status,
                        "start_time": tournament.start_time.isoformat(),
                    },
                )
            )

    return results[:limit]