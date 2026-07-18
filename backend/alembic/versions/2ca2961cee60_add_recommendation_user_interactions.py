"""add_recommendation_user_interactions

Revision ID: 2ca2961cee60
Revises: 017
Create Date: 2026-07-10 23:51:15.713735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ca2961cee60'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # user_interactions table
    op.create_table(
        "user_interactions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()") if is_pg else None),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(30), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("view_duration_ms", sa.Integer(), nullable=True),
        sa.Column("scroll_depth_pct", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("source", sa.String(30), nullable=True),
        sa.Column("position_in_feed", sa.Integer(), nullable=True),
        sa.Column("user_lat", sa.Float(), nullable=True),
        sa.Column("user_lng", sa.Float(), nullable=True),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("hour_of_day", sa.SmallInteger(), nullable=True),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # indexes
    op.create_index("idx_ui_user_id", "user_interactions", ["user_id", "created_at"], postgresql_using="btree" if is_pg else None)
    op.create_index("idx_ui_content", "user_interactions", ["content_id", "action"])
    op.create_index("idx_ui_action", "user_interactions", ["action", "created_at"])
    op.create_index("idx_ui_session", "user_interactions", ["session_id"])

    # Add id default for sqlite if needed
    if not is_pg:
        op.execute("CREATE TRIGGER IF NOT EXISTS set_uuid_user_interactions BEFORE INSERT ON user_interactions FOR EACH ROW WHEN (NEW.id IS NULL) BEGIN UPDATE user_interactions SET id = lower(hex(randomblob(16))) WHERE rowid = NEW.rowid; END;")  # simplistic, better use app default


def downgrade() -> None:
    op.drop_index("idx_ui_session", table_name="user_interactions")
    op.drop_index("idx_ui_action", table_name="user_interactions")
    op.drop_index("idx_ui_content", table_name="user_interactions")
    op.drop_index("idx_ui_user_id", table_name="user_interactions")
    op.drop_table("user_interactions")
