"""Add soft-delete / active flags for gaming place extensions (admin parlor mgmt)

Revision ID: 020_admin_parlor_soft_delete
Revises: 019_users_bio
Create Date: 2026-07-23

Uses raw SQL IF NOT EXISTS so re-runs and partial deploys are safe.
Boolean defaults are true/false (Postgres rejects integer 1/0 for boolean).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "020_admin_parlor_soft_delete"
down_revision: str | None = "019_users_bio"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # IF NOT EXISTS requires PG 9.1+; safe no-op when columns already present.
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'gaming_place_extensions'
          ) THEN
            ALTER TABLE gaming_place_extensions
              ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;
            ALTER TABLE gaming_place_extensions
              ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
            ALTER TABLE gaming_place_extensions
              ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_gaming_place_extensions_is_deleted
          ON gaming_place_extensions (is_deleted)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_gaming_place_extensions_is_active
          ON gaming_place_extensions (is_active)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_gaming_place_extensions_is_active")
    op.execute("DROP INDEX IF EXISTS ix_gaming_place_extensions_is_deleted")
    op.execute(
        "ALTER TABLE gaming_place_extensions DROP COLUMN IF EXISTS deleted_at"
    )
    op.execute(
        "ALTER TABLE gaming_place_extensions DROP COLUMN IF EXISTS is_deleted"
    )
    op.execute(
        "ALTER TABLE gaming_place_extensions DROP COLUMN IF EXISTS is_active"
    )
