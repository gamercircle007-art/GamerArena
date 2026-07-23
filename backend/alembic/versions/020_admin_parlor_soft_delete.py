"""Add soft-delete / active flags for gaming place extensions (admin parlor mgmt)

Revision ID: 020_admin_parlor_soft_delete
Revises: 019_users_bio
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "020_admin_parlor_soft_delete"
down_revision: str | None = "019_users_bio"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return set()
    return {c["name"] for c in inspector.get_columns(table)}


def _index_names(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table not in inspector.get_table_names():
        return set()
    return {i["name"] for i in inspector.get_indexes(table) if i.get("name")}


def upgrade() -> None:
    table = "gaming_place_extensions"
    cols = _column_names(table)
    if not cols:
        return

    if "is_active" not in cols:
        op.add_column(
            table,
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )
    if "is_deleted" not in cols:
        op.add_column(
            table,
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
    if "deleted_at" not in cols:
        op.add_column(
            table,
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )

    indexes = _index_names(table)
    if "ix_gaming_place_extensions_is_deleted" not in indexes:
        op.create_index(
            "ix_gaming_place_extensions_is_deleted",
            table,
            ["is_deleted"],
            unique=False,
        )
    if "ix_gaming_place_extensions_is_active" not in indexes:
        op.create_index(
            "ix_gaming_place_extensions_is_active",
            table,
            ["is_active"],
            unique=False,
        )


def downgrade() -> None:
    table = "gaming_place_extensions"
    indexes = _index_names(table)
    if "ix_gaming_place_extensions_is_active" in indexes:
        op.drop_index("ix_gaming_place_extensions_is_active", table_name=table)
    if "ix_gaming_place_extensions_is_deleted" in indexes:
        op.drop_index("ix_gaming_place_extensions_is_deleted", table_name=table)

    cols = _column_names(table)
    # SQLite < 3.35 cannot DROP COLUMN; skip quietly when unsupported.
    bind = op.get_bind()
    for col in ("deleted_at", "is_deleted", "is_active"):
        if col not in cols:
            continue
        try:
            op.drop_column(table, col)
        except Exception:
            if bind.dialect.name == "sqlite":
                continue
            raise
