"""DMS Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UploadIntentRequest(BaseModel):
    file_type: str
    file_name: str
    file_size: int = Field(gt=0)
    asset_type: str
    context: str
    context_id: UUID | None = None


class UploadIntentResponse(BaseModel):
    asset_id: UUID
    upload_url: str
    cdn_url: str


class ConfirmUploadRequest(BaseModel):
    asset_id: UUID
    width_px: int | None = None
    height_px: int | None = None
    duration_seconds: float | None = None


class ConfirmUploadResponse(BaseModel):
    asset_id: UUID
    cdn_url: str
    thumbnail_url: str | None = None
    status: str


class UpdateContextRequest(BaseModel):
    context_id: UUID


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    uploader_id: UUID | None
    uploader_name: str | None = None
    original_filename: str | None
    file_type: str | None
    asset_type: str
    file_size_bytes: int | None
    file_size_label: str | None
    cdn_url: str
    thumbnail_url: str | None
    width_px: int | None
    height_px: int | None
    duration_seconds: float | None
    context: str
    context_id: UUID | None
    status: str
    is_flagged: bool
    created_at: datetime


class AdminAssetItem(AssetResponse):
    flag_reason: str | None = None


class DmsStatsResponse(BaseModel):
    total_count: int
    total_size_bytes: int
    total_size_label: str
    by_type: dict[str, int]
    by_context: dict[str, int]
    flagged_count: int


class FlagAssetRequest(BaseModel):
    is_flagged: bool
    reason: str | None = None


class StatusAssetRequest(BaseModel):
    status: str


class BulkDeleteRequest(BaseModel):
    asset_ids: list[UUID]