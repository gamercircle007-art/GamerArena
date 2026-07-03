"""Add parlors, social, tournament, and notification tables

Revision ID: 005
Revises: 004
Create Date: 2026-06-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role_enum = postgresql.ENUM("user", "parlor_owner", name="user_role", create_type=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("users", sa.Column("avatar_url", sa.String(length=512), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            server_default="user",
            nullable=False,
        ),
    )
    op.add_column("users", sa.Column("fcm_token", sa.String(length=512), nullable=True))

    op.create_table(
        "parlors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("location", Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("game_types", postgresql.ARRAY(sa.String(length=50)), server_default="{}", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("follower_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("post_count", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_parlors_owner_id"), "parlors", ["owner_id"], unique=False)

    op.create_table(
        "follows",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parlor_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["parlor_id"], ["parlors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "parlor_id", name="uq_follows_user_parlor"),
    )
    op.create_index(op.f("ix_follows_parlor_id"), "follows", ["parlor_id"], unique=False)
    op.create_index(op.f("ix_follows_user_id"), "follows", ["user_id"], unique=False)

    op.create_table(
        "tournaments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parlor_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("game_type", sa.String(length=50), nullable=False),
        sa.Column("format", sa.String(length=50), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_slots", sa.Integer(), nullable=False),
        sa.Column("booked_slots", sa.Integer(), server_default="0", nullable=False),
        sa.Column("entry_fee", sa.Numeric(precision=10, scale=2), server_default="0", nullable=False),
        sa.Column("prizes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rules", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open", nullable=False),
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
        sa.ForeignKeyConstraint(["parlor_id"], ["parlors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tournaments_game_type"), "tournaments", ["game_type"], unique=False)
    op.create_index(op.f("ix_tournaments_parlor_id"), "tournaments", ["parlor_id"], unique=False)
    op.create_index(op.f("ix_tournaments_status"), "tournaments", ["status"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tournament_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("slot_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="confirmed", nullable=False),
        sa.Column("payment_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("payment_id", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "slot_number", name="uq_bookings_tournament_slot"),
        sa.UniqueConstraint("tournament_id", "user_id", name="uq_bookings_tournament_user"),
    )
    op.create_index(op.f("ix_bookings_tournament_id"), "bookings", ["tournament_id"], unique=False)
    op.create_index(op.f("ix_bookings_user_id"), "bookings", ["user_id"], unique=False)

    op.create_table(
        "posts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parlor_id", sa.UUID(), nullable=False),
        sa.Column("tournament_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_urls", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("likes_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments_count", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["parlor_id"], ["parlors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_posts_parlor_id"), "posts", ["parlor_id"], unique=False)
    op.create_index(op.f("ix_posts_tournament_id"), "posts", ["tournament_id"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("likes_count", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comments_parent_id"), "comments", ["parent_id"], unique=False)
    op.create_index(op.f("ix_comments_post_id"), "comments", ["post_id"], unique=False)
    op.create_index(op.f("ix_comments_user_id"), "comments", ["user_id"], unique=False)

    op.create_table(
        "likes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
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
        sa.UniqueConstraint("user_id", "target_type", "target_id", name="uq_likes_user_target"),
    )
    op.create_index(op.f("ix_likes_target_id"), "likes", ["target_id"], unique=False)
    op.create_index(op.f("ix_likes_user_id"), "likes", ["user_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
    op.create_index(op.f("ix_notifications_type"), "notifications", ["type"], unique=False)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_type"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_likes_user_id"), table_name="likes")
    op.drop_index(op.f("ix_likes_target_id"), table_name="likes")
    op.drop_table("likes")

    op.drop_index(op.f("ix_comments_user_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_post_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_parent_id"), table_name="comments")
    op.drop_table("comments")

    op.drop_index(op.f("ix_posts_tournament_id"), table_name="posts")
    op.drop_index(op.f("ix_posts_parlor_id"), table_name="posts")
    op.drop_table("posts")

    op.drop_index(op.f("ix_bookings_user_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_tournament_id"), table_name="bookings")
    op.drop_table("bookings")

    op.drop_index(op.f("ix_tournaments_status"), table_name="tournaments")
    op.drop_index(op.f("ix_tournaments_parlor_id"), table_name="tournaments")
    op.drop_index(op.f("ix_tournaments_game_type"), table_name="tournaments")
    op.drop_table("tournaments")

    op.drop_index(op.f("ix_follows_user_id"), table_name="follows")
    op.drop_index(op.f("ix_follows_parlor_id"), table_name="follows")
    op.drop_table("follows")

    op.drop_index(op.f("ix_parlors_owner_id"), table_name="parlors")
    op.drop_table("parlors")

    op.drop_column("users", "fcm_token")
    op.drop_column("users", "role")
    op.drop_column("users", "avatar_url")

    user_role_enum.drop(op.get_bind(), checkfirst=True)