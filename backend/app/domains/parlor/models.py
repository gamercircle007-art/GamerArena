"""Parlor domain ORM model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableGeography, PortableStringArray


class Parlor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Gaming parlor / venue owned by a registered user."""

    __tablename__ = "parlors"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[object | None] = mapped_column(
        PortableGeography,
        nullable=True,
    )
    game_types: Mapped[list[str]] = mapped_column(
        PortableStringArray,
        nullable=False,
        insert_default=list,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follower_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Parlor id={self.id} name={self.name}>"