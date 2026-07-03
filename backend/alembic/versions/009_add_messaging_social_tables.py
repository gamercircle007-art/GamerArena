"""Add messaging, friends, stories, online status, snap map tables

Revision ID: 009
Revises: 008
Create Date: 2026-06-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("friends_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("followers_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("following_count", sa.Integer(), server_default="0", nullable=False))

    op.create_table(
        "friend_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("receiver_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["receiver_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sender_id", "receiver_id", name="uq_friend_requests_sender_receiver"),
    )
    op.create_index("ix_friend_requests_receiver_status", "friend_requests", ["receiver_id", "status"])

    op.create_table(
        "friendships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user1_id", sa.UUID(), nullable=False),
        sa.Column("user2_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user1_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user2_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user1_id", "user2_id", name="uq_friendships_users"),
    )
    op.create_index("ix_friendships_user1", "friendships", ["user1_id"])
    op.create_index("ix_friendships_user2", "friendships", ["user2_id"])

    op.create_table(
        "user_blocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("blocker_id", sa.UUID(), nullable=False),
        sa.Column("blocked_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["blocked_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blocker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks"),
    )

    op.create_table(
        "user_last_seen",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status_privacy", sa.String(length=20), server_default="friends", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "stories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("media_url", sa.String(length=500), nullable=False),
        sa.Column("media_type", sa.String(length=20), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), server_default="5", nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("privacy", sa.String(length=20), server_default="friends", nullable=False),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stories_user_expires", "stories", ["user_id", "expires_at"])
    op.create_index("ix_stories_expires", "stories", ["expires_at"])

    op.create_table(
        "story_views",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("story_id", sa.UUID(), nullable=False),
        sa.Column("viewer_id", sa.UUID(), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("story_id", "viewer_id", name="uq_story_views"),
    )

    op.create_table(
        "user_locations",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("ghost_mode", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("location_privacy", sa.String(length=20), server_default="friends", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_user_locations_privacy", "user_locations", ["ghost_mode", "location_privacy"])

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("game_tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("website", sa.String(length=200), nullable=True),
        sa.Column("is_private", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allow_messages_from", sa.String(length=20), server_default="friends", nullable=False),
        sa.Column("show_online_status", sa.String(length=20), server_default="friends", nullable=False),
        sa.Column("allow_friend_requests", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("profile_qr_code", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "close_friends",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("friend_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["friend_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "friend_id", name="uq_close_friends"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=20), server_default="direct", nullable=False),
        sa.Column("is_ephemeral", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("theme", sa.String(length=30), server_default="default", nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])

    op.create_table(
        "conversation_participants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_conversation_participants"),
    )
    op.create_index("ix_conversation_participants_user", "conversation_participants", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("message_type", sa.String(length=30), server_default="text", nullable=False),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("is_ephemeral", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("ephemeral_duration", sa.Integer(), server_default="10", nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reply_to_id", sa.UUID(), nullable=True),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lng", sa.Float(), nullable=True),
        sa.Column("sticker_id", sa.String(length=100), nullable=True),
        sa.Column("reactions", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reply_to_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])
    op.create_index("ix_messages_sender", "messages", ["sender_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_sender", table_name="messages")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversation_participants_user", table_name="conversation_participants")
    op.drop_table("conversation_participants")
    op.drop_index("ix_conversations_last_message_at", table_name="conversations")
    op.drop_table("conversations")
    op.drop_table("close_friends")
    op.drop_table("user_profiles")
    op.drop_index("ix_user_locations_privacy", table_name="user_locations")
    op.drop_table("user_locations")
    op.drop_table("story_views")
    op.drop_index("ix_stories_expires", table_name="stories")
    op.drop_index("ix_stories_user_expires", table_name="stories")
    op.drop_table("stories")
    op.drop_table("user_last_seen")
    op.drop_table("user_blocks")
    op.drop_index("ix_friendships_user2", table_name="friendships")
    op.drop_index("ix_friendships_user1", table_name="friendships")
    op.drop_table("friendships")
    op.drop_index("ix_friend_requests_receiver_status", table_name="friend_requests")
    op.drop_table("friend_requests")
    op.drop_column("users", "following_count")
    op.drop_column("users", "followers_count")
    op.drop_column("users", "friends_count")