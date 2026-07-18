"""add_remaining_recommendation_tables

Revision ID: 018addremrec
Revises: 2ca2961cee60
Create Date: 2026-07-10 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '018addremrec'
down_revision: Union[str, None] = '2ca2961cee60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # user_interest_profiles
    op.create_table(
        "user_interest_profiles",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("game_scores", sa.JSON(), nullable=False, server_default='{}'),
        sa.Column("prefers_reels", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("prefers_posts", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("prefers_tournaments", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("prefers_live", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("creator_scores", sa.JSON(), nullable=False, server_default='{}'),
        sa.Column("max_distance_km", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("preferred_city", sa.String(100), nullable=True),
        sa.Column("peak_hour_start", sa.SmallInteger(), nullable=False, server_default="18"),
        sa.Column("peak_hour_end", sa.SmallInteger(), nullable=False, server_default="22"),
        sa.Column("avg_session_duration_min", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("exploration_rate", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("total_interactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("profile_confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("last_computed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # content_engagement_stats (composite PK)
    op.create_table(
        "content_engagement_stats",
        sa.Column("content_id", sa.Uuid(), primary_key=True),
        sa.Column("content_type", sa.String(30), primary_key=True),
        sa.Column("view_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("share_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("save_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hide_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("booking_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_watch_time_ms", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("avg_watch_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("replay_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trending_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("virality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    if is_pg:
        op.create_index("idx_ces_type_score", "content_engagement_stats", ["content_type", "trending_score"], postgresql_using="btree")

    # trending_items
    op.create_table(
        "trending_items",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()") if is_pg else None),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("trending_score", sa.Float(), nullable=False),
        sa.Column("game_category", sa.String(50), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("window", sa.String(10), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_trending_score", "trending_items", ["window", "trending_score"])
    op.create_index("idx_trending_cat", "trending_items", ["game_category", "trending_score"])

    # feed_impressions
    op.create_table(
        "feed_impressions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()") if is_pg else None),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("shown_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("feed_type", sa.String(30), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_impressions_user", "feed_impressions", ["user_id", "shown_at"])
    op.create_index("idx_impressions_dedup", "feed_impressions", ["user_id", "content_id", "content_type"])

    # search_events
    op.create_table(
        "search_events",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()") if is_pg else None),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("query_normalized", sa.String(500), nullable=True),
        sa.Column("results_count", sa.Integer(), nullable=True),
        sa.Column("clicked_content_id", sa.Uuid(), nullable=True),
        sa.Column("clicked_content_type", sa.String(30), nullable=True),
        sa.Column("click_position", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_search_user", "search_events", ["user_id", "created_at"])
    op.create_index("idx_search_query", "search_events", ["query_normalized"])
    op.create_index("idx_search_time", "search_events", ["created_at"])

    # sqlite id triggers if needed (simplified)
    if not is_pg:
        for tbl in ["trending_items", "feed_impressions", "search_events"]:
            op.execute(
                f"CREATE TRIGGER IF NOT EXISTS set_uuid_{tbl} BEFORE INSERT ON {tbl} FOR EACH ROW WHEN (NEW.id IS NULL) BEGIN UPDATE {tbl} SET id = lower(hex(randomblob(16))) WHERE rowid = NEW.rowid; END;"
            )


def downgrade() -> None:
    op.drop_index("idx_search_time", table_name="search_events")
    op.drop_index("idx_search_query", table_name="search_events")
    op.drop_index("idx_search_user", table_name="search_events")
    op.drop_table("search_events")

    op.drop_index("idx_impressions_dedup", table_name="feed_impressions")
    op.drop_index("idx_impressions_user", table_name="feed_impressions")
    op.drop_table("feed_impressions")

    op.drop_index("idx_trending_cat", table_name="trending_items")
    op.drop_index("idx_trending_score", table_name="trending_items")
    op.drop_table("trending_items")

    op.drop_index("idx_ces_type_score", table_name="content_engagement_stats")
    op.drop_table("content_engagement_stats")

    op.drop_table("user_interest_profiles")
