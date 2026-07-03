"""Post ORM model."""

import uuid

from sqlalchemy import ForeignKey, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableTextArray


class Post(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Social post published by a parlor."""

    __tablename__ = "posts"

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("tournaments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list[str]] = mapped_column(
        PortableTextArray,
        nullable=False,
        insert_default=list,
    )
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)