"""Add reels, comments, bookmarks, views, user follows, reports

Revision ID: 008
Revises: 007
Create Date: 2026-06-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

reel_privacy_enum = postgresql.ENUM(
    "public",
    "friends",
    "private",
    "unlisted",
    "international",
    "country_only",
    "followers",
    "nearby",
    "age_restricted",
    name="reel_privacy",
    create_type=True,
)


def upgrade() -> None:
    reel_privacy_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "reels",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("video_url", sa.String(length=1024), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1024), nullable=True),
        sa.Column("cover_url", sa.String(length=1024), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.String(length=100)), server_default="{}", nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("aspect_ratio", sa.String(length=10), server_default="9:16", nullable=False),
        sa.Column("filter_name", sa.String(length=50), server_default="normal", nullable=False),
        sa.Column("music_title", sa.String(length=255), nullable=True),
        sa.Column("music_url", sa.String(length=1024), nullable=True),
        sa.Column("privacy", reel_privacy_enum, server_default="public", nullable=False),
        sa.Column("likes_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("views_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("shares_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("bookmarks_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reels_user_id", "reels", ["user_id"])
    op.create_index("ix_reels_created_at", "reels", ["created_at"])
    op.create_index("ix_reels_privacy", "reels", ["privacy"])

    op.create_table(
        "reel_comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reel_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("likes_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reel_id"], ["reels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["reel_comments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reel_comments_reel_id", "reel_comments", ["reel_id"])
    op.create_index("ix_reel_comments_parent_id", "reel_comments", ["parent_id"])

    op.create_table(
        "reel_bookmarks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("reel_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reel_id"], ["reels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "reel_id", name="uq_reel_bookmarks_user_reel"),
    )

    op.create_table(
        "reel_views",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reel_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reel_id"], ["reels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reel_views_reel_id", "reel_views", ["reel_id"])

    op.create_table(
        "user_follows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("follower_id", sa.UUID(), nullable=False),
        sa.Column("following_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["following_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follower_id", "following_id", name="uq_user_follows_pair"),
    )
    op.create_index("ix_user_follows_following_id", "user_follows", ["following_id"])

    op.create_table(
        "reel_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reel_id", sa.UUID(), nullable=False),
        sa.Column("reporter_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reel_id"], ["reels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("reel_reports")
    op.drop_index("ix_user_follows_following_id", table_name="user_follows")
    op.drop_table("user_follows")
    op.drop_index("ix_reel_views_reel_id", table_name="reel_views")
    op.drop_table("reel_views")
    op.drop_table("reel_bookmarks")
    op.drop_index("ix_reel_comments_parent_id", table_name="reel_comments")
    op.drop_index("ix_reel_comments_reel_id", table_name="reel_comments")
    op.drop_table("reel_comments")
    op.drop_index("ix_reels_privacy", table_name="reels")
    op.drop_index("ix_reels_created_at", table_name="reels")
    op.drop_index("ix_reels_user_id", table_name="reels")
    op.drop_table("reels")
    reel_privacy_enum.drop(op.get_bind(), checkfirst=True)