"""Follow relationship between users and parlors."""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Follow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User follows a parlor."""

    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("user_id", "parlor_id", name="uq_follows_user_parlor"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("gaming_places.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )