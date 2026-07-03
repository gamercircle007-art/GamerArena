"""Helpers to resolve media asset IDs to CDN URLs across domains."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.dms.models import MediaAsset


async def resolve_asset_url(session: AsyncSession, asset_id: UUID | str | None) -> str | None:
    if not asset_id:
        return None
    if isinstance(asset_id, str):
        asset_id = UUID(asset_id)
    row = await session.execute(
        select(MediaAsset.cdn_url).where(
            MediaAsset.id == asset_id,
            MediaAsset.status != "deleted",
        )
    )
    return row.scalar_one_or_none()


async def resolve_asset_urls(
    session: AsyncSession, asset_ids: list[UUID | str] | None
) -> list[str]:
    if not asset_ids:
        return []
    urls: list[str] = []
    for aid in asset_ids:
        url = await resolve_asset_url(session, aid)
        if url:
            urls.append(url)
    return urls