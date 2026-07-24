"""Extend posts table for full upload/create content flow (YouTube-style Post/Short/Video/Live)

Revision ID: 017
Revises: 016
Create Date: 2026-07-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _array_type(item_type):
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.ARRAY(item_type)
    return sa.JSON()


def upgrade() -> None:
    # Core type/visibility
    op.add_column("posts", sa.Column("post_type", sa.String(20), nullable=False, server_default="post"))
    op.add_column("posts", sa.Column("title", sa.String(300), nullable=True))
    op.add_column("posts", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("visibility", sa.String(20), nullable=False, server_default="public"))
    op.add_column("posts", sa.Column("audience", sa.String(20), nullable=False, server_default="everyone"))

    # Game/algorithm fields
    op.add_column("posts", sa.Column("game_types", _array_type(sa.String()), nullable=True))
    op.add_column("posts", sa.Column("tags", _array_type(sa.String()), nullable=True))
    op.add_column("posts", sa.Column("hashtags", _array_type(sa.String()), nullable=True))
    op.add_column("posts", sa.Column("mentions", _array_type(sa.String()), nullable=True))

    # Relations
    op.add_column("posts", sa.Column("location_parlor_id", sa.Uuid(), nullable=True))
    # tournament_id already exists from earlier migration

    # Community
    op.add_column("posts", sa.Column("allow_comments", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("posts", sa.Column("allow_remix", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("posts", sa.Column("allow_duet", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("posts", sa.Column("hide_likes", sa.Boolean(), nullable=False, server_default=sa.false()))

    # Attributes
    op.add_column("posts", sa.Column("is_ai_content", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("posts", sa.Column("is_paid_promo", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("posts", sa.Column("is_for_kids", sa.Boolean(), nullable=False, server_default=sa.false()))

    # Draft/schedule
    op.add_column("posts", sa.Column("is_draft", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("posts", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))

    # Video specific
    op.add_column("posts", sa.Column("duration_seconds", sa.Float(), nullable=True))
    op.add_column("posts", sa.Column("thumbnail_asset_id", sa.Uuid(), nullable=True))
    op.add_column("posts", sa.Column("video_asset_id", sa.Uuid(), nullable=True))
    op.add_column("posts", sa.Column("processing_status", sa.String(20), nullable=False, server_default="ready"))

    # Add FKs where useful (for PG)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_foreign_key("fk_posts_location_parlor", "posts", "gaming_places", ["location_parlor_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key("fk_posts_thumbnail_asset", "posts", "media_assets", ["thumbnail_asset_id"], ["id"], ondelete="SET NULL")
        op.create_foreign_key("fk_posts_video_asset", "posts", "media_assets", ["video_asset_id"], ["id"], ondelete="SET NULL")

    # Indexes
    op.create_index("ix_posts_post_type", "posts", ["post_type"])
    op.create_index("ix_posts_visibility", "posts", ["visibility"])
    op.create_index("ix_posts_created_at", "posts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_posts_created_at", table_name="posts")
    op.drop_index("ix_posts_visibility", table_name="posts")
    op.drop_index("ix_posts_post_type", table_name="posts")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("fk_posts_video_asset", "posts", type_="foreignkey")
        op.drop_constraint("fk_posts_thumbnail_asset", "posts", type_="foreignkey")
        op.drop_constraint("fk_posts_location_parlor", "posts", type_="foreignkey")

    op.drop_column("posts", "processing_status")
    op.drop_column("posts", "video_asset_id")
    op.drop_column("posts", "thumbnail_asset_id")
    op.drop_column("posts", "duration_seconds")
    op.drop_column("posts", "scheduled_at")
    op.drop_column("posts", "is_draft")
    op.drop_column("posts", "is_for_kids")
    op.drop_column("posts", "is_paid_promo")
    op.drop_column("posts", "is_ai_content")
    op.drop_column("posts", "hide_likes")
    op.drop_column("posts", "allow_duet")
    op.drop_column("posts", "allow_remix")
    op.drop_column("posts", "allow_comments")
    op.drop_column("posts", "tournament_id")
    op.drop_column("posts", "location_parlor_id")
    op.drop_column("posts", "mentions")
    op.drop_column("posts", "hashtags")
    op.drop_column("posts", "tags")
    op.drop_column("posts", "game_types")
    op.drop_column("posts", "audience")
    op.drop_column("posts", "visibility")
    op.drop_column("posts", "description")
    op.drop_column("posts", "title")
    op.drop_column("posts", "post_type")
