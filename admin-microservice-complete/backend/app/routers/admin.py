from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.deps import AdminDep
from app.schemas import PaginatedResponse, UserResponse
from app.services.mock_store import store

router = APIRouter(prefix="/admin", tags=["Admin"])


class UserPatch(BaseModel):
    is_active: bool | None = None
    role: str | None = None


class ParlorVerifyPatch(BaseModel):
    is_verified: bool


@router.get("/stats")
async def stats(_: AdminDep) -> dict:
    return store.stats()


@router.get("/analytics")
async def analytics(_: AdminDep, period: str = "30d") -> dict:
    return store.analytics(period)


@router.get("/users")
async def list_users(
    _: AdminDep,
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> dict:
    return store.list_users(page=page, limit=limit, search=search, role=role, is_active=is_active)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, _: AdminDep) -> UserResponse:
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, body: UserPatch, _: AdminDep) -> UserResponse:
    data = body.model_dump(exclude_unset=True)
    user = store.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, _: AdminDep) -> None:
    if not store.delete_user(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/parlors")
async def list_parlors(
    _: AdminDep,
    page: int = 1,
    limit: int = 20,
    is_verified: bool | None = None,
    search: str | None = None,
) -> dict:
    return store.list_parlors(page=page, limit=limit, is_verified=is_verified, search=search)


@router.patch("/parlors/{parlor_id}/verify")
async def verify_parlor(parlor_id: str, body: ParlorVerifyPatch, _: AdminDep) -> dict:
    parlor = store.verify_parlor(parlor_id, body.is_verified)
    if not parlor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlor not found")
    return parlor


@router.delete("/parlors/{parlor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parlor(parlor_id: str, _: AdminDep) -> None:
    if not store.delete_parlor(parlor_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlor not found")


@router.get("/bookings")
async def list_bookings(_: AdminDep, page: int = 1, limit: int = 20, user_id: str | None = None) -> dict:
    return store.list_bookings(user_id=user_id, page=page, limit=limit)


@router.get("/likes")
async def list_likes(_: AdminDep, page: int = 1, limit: int = 20, user_id: str | None = None) -> dict:
    return store.list_likes(user_id=user_id, page=page, limit=limit)


@router.get("/posts")
async def list_posts(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.get("/comments")
async def list_comments(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.get("/tournaments")
async def list_tournaments(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.get("/events")
async def list_events(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.get("/community")
async def list_community(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.get("/ratings")
async def list_ratings(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.get("/geo-activity")
async def geo_activity(_: AdminDep, page: int = 1, limit: int = 20) -> PaginatedResponse:
    return PaginatedResponse(items=[], total=0, page=page, limit=limit, has_more=False)


@router.post("/notifications/broadcast")
async def broadcast(_: AdminDep, body: dict) -> dict:
    return {"sent_to": 1250}