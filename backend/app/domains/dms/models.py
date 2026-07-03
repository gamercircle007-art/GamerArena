"""DMS — centralized media asset ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MediaAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Single source of truth for all uploaded media in the app."""

    __tablename__ = "media_assets"

    uploader_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_size_label: Mapped[str | None] = mapped_column(String(20), nullable=True)

    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    cdn_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    blurhash: Mapped[str | None] = mapped_column(String(100), nullable=True)

    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    context: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    context_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    flagged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    uploader = relationship("User", foreign_keys=[uploader_id], lazy="joined")

    @property
    def is_image(self) -> bool:
        return self.asset_type == "image"

    @property
    def is_video(self) -> bool:
        return self.asset_type == "video"

    @property
    def is_document(self) -> bool:
        return self.asset_type == "document"

    @property
    def is_audio(self) -> bool:
        return self.asset_type == "audio"