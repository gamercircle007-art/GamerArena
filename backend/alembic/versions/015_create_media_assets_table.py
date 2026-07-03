"""Create media_assets table

Revision ID: 015
Revises: 014
Create Date: 2026-07-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=True),
        sa.Column("file_type", sa.String(length=100), nullable=True),
        sa.Column("asset_type", sa.String(length=20), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("file_size_label", sa.String(length=20), nullable=True),
        sa.Column("s3_key", sa.String(length=1000), nullable=False),
        sa.Column("s3_bucket", sa.String(length=100), nullable=False),
        sa.Column("cdn_url", sa.String(length=1000), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
        sa.Column("blurhash", sa.String(length=100), nullable=True),
        sa.Column("width_px", sa.Integer(), nullable=True),
        sa.Column("height_px", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("context", sa.String(length=50), nullable=False),
        sa.Column("context_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("is_flagged", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("flag_reason", sa.Text(), nullable=True),
        sa.Column("flagged_by", sa.Uuid(), nullable=True),
        sa.Column("flagged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["flagged_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_media_assets_uploader", "media_assets", ["uploader_id"])
    op.create_index("idx_media_assets_context", "media_assets", ["context", "context_id"])
    op.create_index("idx_media_assets_type", "media_assets", ["asset_type"])
    op.create_index("idx_media_assets_status", "media_assets", ["status"])
    op.create_index("idx_media_assets_created", "media_assets", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_media_assets_created", table_name="media_assets")
    op.drop_index("idx_media_assets_status", table_name="media_assets")
    op.drop_index("idx_media_assets_type", table_name="media_assets")
    op.drop_index("idx_media_assets_context", table_name="media_assets")
    op.drop_index("idx_media_assets_uploader", table_name="media_assets")
    op.drop_table("media_assets")