"""DMS business logic — upload intent, confirm, resolve, admin ops."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.domains.common.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.domains.dms.models import MediaAsset
from app.domains.dms.schemas import (
    AdminAssetItem,
    AssetResponse,
    ConfirmUploadResponse,
    DmsStatsResponse,
    UploadIntentResponse,
)
from app.domains.user.models import User

ALLOWED_MIME_TYPES: dict[str, list[str]] = {
    "image": ["image/jpeg", "image/png", "image/webp", "image/gif"],
    "video": ["video/mp4", "video/quicktime", "video/webm"],
    "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/m4a"],
    "document": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ],
}

MAX_FILE_SIZES: dict[str, int] = {
    "image": 15 * 1024 * 1024,
    "video": 500 * 1024 * 1024,
    "audio": 50 * 1024 * 1024,
    "document": 25 * 1024 * 1024,
}

UPLOAD_URL_EXPIRY = 900


def _format_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _s3_key(asset_type: str, asset_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"media/{asset_type}/{asset_id[:2]}/{asset_id}.{ext}"


def _cdn_base(settings: Settings) -> str:
    if settings.aws_cloudfront_domain:
        return f"https://{settings.aws_cloudfront_domain}"
    return "https://dev-cdn.example.com"


class DmsService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def _s3_client(self):
        import boto3

        return boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )

    async def create_upload_intent(
        self,
        uploader_id: UUID,
        file_type: str,
        file_name: str,
        file_size: int,
        asset_type: str,
        context: str,
        context_id: UUID | None,
    ) -> UploadIntentResponse:
        if asset_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"Unsupported asset_type: {asset_type}")
        if file_type not in ALLOWED_MIME_TYPES[asset_type]:
            raise ValidationError(f"File type {file_type} not allowed for {asset_type}")
        if file_size > MAX_FILE_SIZES[asset_type]:
            max_mb = MAX_FILE_SIZES[asset_type] // (1024 * 1024)
            raise ValidationError(f"File too large. Max {max_mb}MB for {asset_type}")

        asset_id = uuid.uuid4()
        key = _s3_key(asset_type, str(asset_id), file_name)
        cdn_url = f"{_cdn_base(self.settings)}/{key}"
        bucket = self.settings.aws_s3_bucket or "dev-bucket"

        if self.settings.aws_s3_bucket:
            client = self._s3_client()
            upload_url = client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": bucket,
                    "Key": key,
                    "ContentType": file_type,
                },
                ExpiresIn=UPLOAD_URL_EXPIRY,
            )
        else:
            upload_url = f"{_cdn_base(self.settings)}/upload-stub/{key}"

        asset = MediaAsset(
            id=asset_id,
            uploader_id=uploader_id,
            original_filename=file_name,
            file_type=file_type,
            asset_type=asset_type,
            file_size_bytes=file_size,
            file_size_label=_format_size(file_size),
            s3_key=key,
            s3_bucket=bucket,
            cdn_url=cdn_url,
            context=context,
            context_id=context_id,
            status="processing",
        )
        self.session.add(asset)
        await self.session.commit()

        return UploadIntentResponse(
            asset_id=asset_id,
            upload_url=upload_url,
            cdn_url=cdn_url,
        )

    async def confirm_upload(
        self,
        asset_id: UUID,
        uploader_id: UUID,
        width_px: int | None,
        height_px: int | None,
        duration_seconds: float | None,
    ) -> ConfirmUploadResponse:
        asset = (
            await self.session.execute(
                select(MediaAsset).where(
                    MediaAsset.id == asset_id,
                    MediaAsset.uploader_id == uploader_id,
                    MediaAsset.status == "processing",
                )
            )
        ).scalar_one_or_none()

        if not asset:
            raise NotFoundError("Asset not found or already confirmed")

        if self.settings.aws_s3_bucket:
            try:
                self._s3_client().head_object(Bucket=asset.s3_bucket, Key=asset.s3_key)
            except Exception as exc:
                raise ValidationError("File not found in S3. Upload may have failed.") from exc

        asset.width_px = width_px
        asset.height_px = height_px
        asset.duration_seconds = duration_seconds
        asset.status = "active"

        if asset.asset_type == "video":
            try:
                from app.tasks.media_tasks import generate_video_thumbnail

                generate_video_thumbnail.delay(str(asset.id), asset.cdn_url)
            except Exception:
                pass

        await self.session.commit()
        await self.session.refresh(asset)

        return ConfirmUploadResponse(
            asset_id=asset.id,
            cdn_url=asset.cdn_url,
            thumbnail_url=asset.thumbnail_url,
            status=asset.status,
        )

    async def get_asset(self, asset_id: UUID) -> AssetResponse:
        asset = await self._get_active_asset(asset_id)
        return self._to_asset_response(asset)

    async def soft_delete_asset(self, asset_id: UUID, requester_id: UUID) -> None:
        asset = (
            await self.session.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset not found")
        if asset.uploader_id != requester_id:
            raise AuthenticationError("Not your asset")
        asset.status = "deleted"
        asset.deleted_at = datetime.now(UTC)
        await self.session.commit()

    async def update_context(self, asset_id: UUID, context_id: UUID, requester_id: UUID) -> AssetResponse:
        asset = (
            await self.session.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset not found")
        if asset.uploader_id != requester_id:
            raise AuthenticationError("Not your asset")
        asset.context_id = context_id
        await self.session.commit()
        await self.session.refresh(asset)
        return self._to_asset_response(asset)

    async def list_assets(
        self,
        *,
        context: str | None = None,
        context_id: UUID | None = None,
        asset_type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        query = select(MediaAsset).where(MediaAsset.status != "deleted")
        if context:
            query = query.where(MediaAsset.context == context)
        if context_id:
            query = query.where(MediaAsset.context_id == context_id)
        if asset_type:
            query = query.where(MediaAsset.asset_type == asset_type)

        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * limit
        rows = (
            await self.session.execute(
                query.order_by(MediaAsset.created_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().all()

        return {
            "items": [self._to_asset_response(a) for a in rows],
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": page * limit < total,
        }

    async def admin_list_assets(
        self,
        *,
        asset_type: str | None = None,
        context: str | None = None,
        uploader_id: UUID | None = None,
        is_flagged: bool | None = None,
        status: str | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        query = select(MediaAsset)
        if asset_type:
            query = query.where(MediaAsset.asset_type == asset_type)
        if context:
            query = query.where(MediaAsset.context == context)
        if uploader_id:
            query = query.where(MediaAsset.uploader_id == uploader_id)
        if is_flagged is not None:
            query = query.where(MediaAsset.is_flagged.is_(is_flagged))
        if status:
            query = query.where(MediaAsset.status == status)
        if search:
            query = query.where(
                or_(
                    MediaAsset.original_filename.ilike(f"%{search}%"),
                    MediaAsset.cdn_url.ilike(f"%{search}%"),
                )
            )
        if date_from:
            query = query.where(MediaAsset.created_at >= date_from)
        if date_to:
            query = query.where(MediaAsset.created_at <= date_to)

        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * limit
        rows = (
            await self.session.execute(
                query.order_by(MediaAsset.created_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().all()

        return {
            "items": [self._to_admin_item(a) for a in rows],
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": page * limit < total,
        }

    async def admin_stats(self) -> DmsStatsResponse:
        total_count = await self.session.scalar(
            select(func.count()).select_from(MediaAsset).where(MediaAsset.status != "deleted")
        ) or 0
        total_size = await self.session.scalar(
            select(func.coalesce(func.sum(MediaAsset.file_size_bytes), 0)).where(
                MediaAsset.status != "deleted"
            )
        ) or 0
        flagged_count = await self.session.scalar(
            select(func.count()).select_from(MediaAsset).where(MediaAsset.is_flagged.is_(True))
        ) or 0

        by_type: dict[str, int] = {}
        type_rows = await self.session.execute(
            select(MediaAsset.asset_type, func.count())
            .where(MediaAsset.status != "deleted")
            .group_by(MediaAsset.asset_type)
        )
        for asset_type, count in type_rows.all():
            by_type[asset_type] = count

        by_context: dict[str, int] = {}
        ctx_rows = await self.session.execute(
            select(MediaAsset.context, func.count())
            .where(MediaAsset.status != "deleted")
            .group_by(MediaAsset.context)
        )
        for ctx, count in ctx_rows.all():
            by_context[ctx] = count

        return DmsStatsResponse(
            total_count=total_count,
            total_size_bytes=int(total_size),
            total_size_label=_format_size(int(total_size)),
            by_type=by_type,
            by_context=by_context,
            flagged_count=flagged_count,
        )

    async def admin_orphans(self, page: int = 1, limit: int = 20) -> dict:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        query = select(MediaAsset).where(
            and_(
                MediaAsset.context_id.is_(None),
                MediaAsset.created_at < cutoff,
                MediaAsset.status == "active",
            )
        )
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * limit
        rows = (
            await self.session.execute(
                query.order_by(MediaAsset.created_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().all()
        return {
            "items": [self._to_admin_item(a) for a in rows],
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": page * limit < total,
        }

    async def admin_hard_delete(self, asset_id: UUID) -> None:
        asset = (
            await self.session.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset not found")

        if self.settings.aws_s3_bucket:
            try:
                self._s3_client().delete_object(Bucket=asset.s3_bucket, Key=asset.s3_key)
                if asset.thumbnail_url and "/media/thumbnails/" in asset.thumbnail_url:
                    thumb_key = asset.thumbnail_url.split(_cdn_base(self.settings) + "/")[-1]
                    self._s3_client().delete_object(Bucket=asset.s3_bucket, Key=thumb_key)
            except Exception:
                pass

        await self.session.delete(asset)
        await self.session.commit()

    async def admin_flag(self, asset_id: UUID, is_flagged: bool, reason: str | None, admin_id: UUID) -> AdminAssetItem:
        asset = (
            await self.session.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset not found")
        asset.is_flagged = is_flagged
        asset.flag_reason = reason if is_flagged else None
        asset.flagged_by = admin_id if is_flagged else None
        asset.flagged_at = datetime.now(UTC) if is_flagged else None
        if is_flagged:
            asset.status = "flagged"
        elif asset.status == "flagged":
            asset.status = "active"
        await self.session.commit()
        await self.session.refresh(asset)
        return self._to_admin_item(asset)

    async def admin_set_status(self, asset_id: UUID, status: str) -> AdminAssetItem:
        asset = (
            await self.session.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset not found")
        asset.status = status
        if status == "deleted":
            asset.deleted_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(asset)
        return self._to_admin_item(asset)

    async def admin_bulk_delete(self, asset_ids: list[UUID]) -> dict:
        deleted = 0
        for asset_id in asset_ids:
            try:
                await self.admin_hard_delete(asset_id)
                deleted += 1
            except NotFoundError:
                continue
        return {"deleted": deleted, "requested": len(asset_ids)}

    async def resolve_cdn_url(self, asset_id: UUID | None) -> str | None:
        if not asset_id:
            return None
        try:
            asset = await self._get_active_asset(asset_id)
            return asset.cdn_url
        except NotFoundError:
            return None

    async def _get_active_asset(self, asset_id: UUID) -> MediaAsset:
        asset = (
            await self.session.execute(
                select(MediaAsset).where(
                    MediaAsset.id == asset_id,
                    MediaAsset.status != "deleted",
                )
            )
        ).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset not found")
        return asset

    def _to_asset_response(self, asset: MediaAsset) -> AssetResponse:
        uploader_name = None
        if asset.uploader:
            uploader_name = asset.uploader.full_name or asset.uploader.username
        return AssetResponse(
            id=asset.id,
            uploader_id=asset.uploader_id,
            uploader_name=uploader_name,
            original_filename=asset.original_filename,
            file_type=asset.file_type,
            asset_type=asset.asset_type,
            file_size_bytes=asset.file_size_bytes,
            file_size_label=asset.file_size_label,
            cdn_url=asset.cdn_url,
            thumbnail_url=asset.thumbnail_url,
            width_px=asset.width_px,
            height_px=asset.height_px,
            duration_seconds=asset.duration_seconds,
            context=asset.context,
            context_id=asset.context_id,
            status=asset.status,
            is_flagged=asset.is_flagged,
            created_at=asset.created_at,
        )

    def _to_admin_item(self, asset: MediaAsset) -> AdminAssetItem:
        base = self._to_asset_response(asset)
        return AdminAssetItem(**base.model_dump(), flag_reason=asset.flag_reason)