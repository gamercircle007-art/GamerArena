"""DMS public API routes."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, SettingsDep
from app.domains.dms.schemas import (
    AssetResponse,
    ConfirmUploadRequest,
    ConfirmUploadResponse,
    UpdateContextRequest,
    UploadIntentRequest,
    UploadIntentResponse,
)
from app.domains.dms.service import DmsService

router = APIRouter(prefix="/dms", tags=["DMS"])


@router.post("/upload-intent", response_model=UploadIntentResponse)
async def upload_intent(
    body: UploadIntentRequest,
    db: DbSessionDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> UploadIntentResponse:
    return await DmsService(db, settings).create_upload_intent(
        uploader_id=current_user.id,
        file_type=body.file_type,
        file_name=body.file_name,
        file_size=body.file_size,
        asset_type=body.asset_type,
        context=body.context,
        context_id=body.context_id,
    )


@router.post("/confirm-upload", response_model=ConfirmUploadResponse)
async def confirm_upload(
    body: ConfirmUploadRequest,
    db: DbSessionDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> ConfirmUploadResponse:
    return await DmsService(db, settings).confirm_upload(
        asset_id=body.asset_id,
        uploader_id=current_user.id,
        width_px=body.width_px,
        height_px=body.height_px,
        duration_seconds=body.duration_seconds,
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: DbSessionDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> AssetResponse:
    _ = current_user
    return await DmsService(db, settings).get_asset(asset_id)


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: DbSessionDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> None:
    await DmsService(db, settings).soft_delete_asset(asset_id, current_user.id)


@router.patch("/assets/{asset_id}/context", response_model=AssetResponse)
async def update_asset_context(
    asset_id: UUID,
    body: UpdateContextRequest,
    db: DbSessionDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> AssetResponse:
    return await DmsService(db, settings).update_context(
        asset_id, body.context_id, current_user.id
    )


@router.get("/assets")
async def list_assets(
    db: DbSessionDep,
    settings: SettingsDep,
    current_user: CurrentUserDep,
    context: str | None = None,
    context_id: UUID | None = None,
    type: str | None = Query(None, alias="type"),
    page: int = 1,
    limit: int = Query(20, le=100),
) -> dict:
    _ = current_user
    return await DmsService(db, settings).list_assets(
        context=context,
        context_id=context_id,
        asset_type=type,
        page=page,
        limit=limit,
    )