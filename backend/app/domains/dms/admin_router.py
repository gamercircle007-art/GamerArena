"""Admin DMS API routes."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, SettingsDep
from app.domains.dms.schemas import (
    AdminAssetItem,
    BulkDeleteRequest,
    DmsStatsResponse,
    FlagAssetRequest,
    StatusAssetRequest,
)
from app.domains.dms.service import DmsService
from app.domains.user.models import UserRole

router = APIRouter(prefix="/admin/dms", tags=["Admin DMS"])


def _require_admin(user) -> None:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


@router.get("")
async def admin_list_dms(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
    type: str | None = Query(None, alias="type"),
    context: str | None = None,
    uploader_id: UUID | None = None,
    is_flagged: bool | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    limit: int = Query(20, le=100),
) -> dict:
    _require_admin(current_user)
    return await DmsService(db, settings).admin_list_assets(
        asset_type=type,
        context=context,
        uploader_id=uploader_id,
        is_flagged=is_flagged,
        status=status,
        search=search,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )


@router.get("/stats", response_model=DmsStatsResponse)
async def admin_dms_stats(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> DmsStatsResponse:
    _require_admin(current_user)
    return await DmsService(db, settings).admin_stats()


@router.get("/orphans")
async def admin_dms_orphans(
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
    page: int = 1,
    limit: int = Query(20, le=100),
) -> dict:
    _require_admin(current_user)
    return await DmsService(db, settings).admin_orphans(page=page, limit=limit)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_hard_delete(
    asset_id: UUID,
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> None:
    _require_admin(current_user)
    await DmsService(db, settings).admin_hard_delete(asset_id)


@router.patch("/{asset_id}/flag", response_model=AdminAssetItem)
async def admin_flag_asset(
    asset_id: UUID,
    body: FlagAssetRequest,
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> AdminAssetItem:
    _require_admin(current_user)
    return await DmsService(db, settings).admin_flag(
        asset_id, body.is_flagged, body.reason, current_user.id
    )


@router.patch("/{asset_id}/status", response_model=AdminAssetItem)
async def admin_set_status(
    asset_id: UUID,
    body: StatusAssetRequest,
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> AdminAssetItem:
    _require_admin(current_user)
    return await DmsService(db, settings).admin_set_status(asset_id, body.status)


@router.post("/bulk-delete")
async def admin_bulk_delete(
    body: BulkDeleteRequest,
    current_user: CurrentUserDep,
    db: DbSessionDep,
    settings: SettingsDep,
) -> dict:
    _require_admin(current_user)
    return await DmsService(db, settings).admin_bulk_delete(body.asset_ids)