"""Add asset_id columns to existing tables

Revision ID: 016
Revises: 015
Create Date: 2026-07-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_array_type():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.ARRAY(sa.Uuid())
    return sa.JSON()


def upgrade() -> None:
    uuid_fk = sa.Uuid()

    op.add_column("users", sa.Column("avatar_asset_id", uuid_fk, nullable=True))
    op.create_foreign_key(
        "fk_users_avatar_asset_id",
        "users",
        "media_assets",
        ["avatar_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("parlors", sa.Column("logo_asset_id", uuid_fk, nullable=True))
    op.add_column("parlors", sa.Column("cover_asset_id", uuid_fk, nullable=True))
    op.create_foreign_key(
        "fk_parlors_logo_asset_id",
        "parlors",
        "media_assets",
        ["logo_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_parlors_cover_asset_id",
        "parlors",
        "media_assets",
        ["cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "posts",
        sa.Column("media_asset_ids", _uuid_array_type(), nullable=True),
    )

    op.add_column("stories", sa.Column("asset_id", uuid_fk, nullable=True))
    op.create_foreign_key(
        "fk_stories_asset_id",
        "stories",
        "media_assets",
        ["asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("messages", sa.Column("asset_id", uuid_fk, nullable=True))
    op.create_foreign_key(
        "fk_messages_asset_id",
        "messages",
        "media_assets",
        ["asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "parlour_ratings",
        sa.Column("review_asset_ids", _uuid_array_type(), nullable=True),
    )

    op.add_column("reels", sa.Column("video_asset_id", uuid_fk, nullable=True))
    op.add_column("reels", sa.Column("cover_asset_id", uuid_fk, nullable=True))
    op.create_foreign_key(
        "fk_reels_video_asset_id",
        "reels",
        "media_assets",
        ["video_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_reels_cover_asset_id",
        "reels",
        "media_assets",
        ["cover_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("gaming_places", sa.Column("image_asset_id", uuid_fk, nullable=True))
    op.create_foreign_key(
        "fk_gaming_places_image_asset_id",
        "gaming_places",
        "media_assets",
        ["image_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_gaming_places_image_asset_id", "gaming_places", type_="foreignkey")
    op.drop_column("gaming_places", "image_asset_id")

    op.drop_constraint("fk_reels_cover_asset_id", "reels", type_="foreignkey")
    op.drop_constraint("fk_reels_video_asset_id", "reels", type_="foreignkey")
    op.drop_column("reels", "cover_asset_id")
    op.drop_column("reels", "video_asset_id")

    op.drop_column("parlour_ratings", "review_asset_ids")

    op.drop_constraint("fk_messages_asset_id", "messages", type_="foreignkey")
    op.drop_column("messages", "asset_id")

    op.drop_constraint("fk_stories_asset_id", "stories", type_="foreignkey")
    op.drop_column("stories", "asset_id")

    op.drop_column("posts", "media_asset_ids")

    op.drop_constraint("fk_parlors_cover_asset_id", "parlors", type_="foreignkey")
    op.drop_constraint("fk_parlors_logo_asset_id", "parlors", type_="foreignkey")
    op.drop_column("parlors", "cover_asset_id")
    op.drop_column("parlors", "logo_asset_id")

    op.drop_constraint("fk_users_avatar_asset_id", "users", type_="foreignkey")
    op.drop_column("users", "avatar_asset_id")