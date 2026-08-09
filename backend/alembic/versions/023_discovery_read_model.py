"""Discovery read model: geography, denormalized columns, indexes

Adds PostGIS location + GiST, pg_trgm search_doc, available_now,
rating_score, amenities_mask, price_paise, thumb_url on gaming_places.
Partial indexes match API WHERE predicates.

Revision ID: 023_discovery_read_model
Revises: 022_club_management
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "023_discovery_read_model"
down_revision: str | None = "022_club_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # --- columns (portable) ---
    op.add_column(
        "gaming_places",
        sa.Column("available_now", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "gaming_places",
        sa.Column("rating_score", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "gaming_places",
        sa.Column("amenities_mask", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "gaming_places",
        sa.Column("price_paise", sa.Integer(), nullable=True),
    )
    op.add_column(
        "gaming_places",
        sa.Column("thumb_url", sa.String(length=1000), nullable=True),
    )
    op.add_column(
        "gaming_places",
        sa.Column("search_doc", sa.Text(), nullable=True),
    )
    op.add_column(
        "gaming_places",
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
    )

    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        # Stored geography for KNN / ST_DWithin (GiST-friendly)
        op.execute(
            """
            ALTER TABLE gaming_places
            ADD COLUMN IF NOT EXISTS location geography(Point, 4326)
            """
        )
        op.execute(
            """
            UPDATE gaming_places
            SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL
              AND location IS NULL
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_gaming_places_location
            ON gaming_places USING GIST (location)
            """
        )

        # Seed search_doc + thumb + price from extension
        op.execute(
            """
            UPDATE gaming_places gp
            SET search_doc = lower(coalesce(gp.name, '') || ' ' ||
                                   coalesce(gp.address, '') || ' ' ||
                                   coalesce(gp.primary_type, ''))
            WHERE search_doc IS NULL
            """
        )
        op.execute(
            """
            UPDATE gaming_places gp
            SET thumb_url = coalesce(gp.thumb_url, gp.image_url)
            WHERE gp.thumb_url IS NULL AND gp.image_url IS NOT NULL
            """
        )
        op.execute(
            """
            UPDATE gaming_places gp
            SET price_paise = CASE
                WHEN e.price_per_hour IS NULL THEN NULL
                ELSE round(e.price_per_hour * 100)::int
            END
            FROM gaming_place_extensions e
            WHERE e.gaming_place_id = gp.id
              AND gp.price_paise IS NULL
            """
        )
        op.execute(
            """
            UPDATE gaming_places gp
            SET rating_score = coalesce(gp.rating, 0),
                review_count = coalesce(gp.user_ratings_total, 0)
            WHERE gp.rating_score = 0 AND gp.rating IS NOT NULL
            """
        )

        # Partial indexes — predicates must match API WHERE
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_gaming_places_available_now
            ON gaming_places (available_now)
            WHERE available_now = true
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_gaming_places_rating_score
            ON gaming_places (rating_score DESC, id)
            WHERE available_now = true OR available_now = false
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_gaming_places_search_doc_trgm
            ON gaming_places USING GIN (search_doc gin_trgm_ops)
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_gaming_places_amenities_mask
            ON gaming_places (amenities_mask)
            WHERE amenities_mask > 0
            """
        )
        op.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_gaming_places_lat_lng
            ON gaming_places (latitude, longitude)
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """
        )

        # Keep location + search_doc in sync on write
        op.execute(
            """
            CREATE OR REPLACE FUNCTION gaming_places_discovery_touch()
            RETURNS trigger AS $$
            BEGIN
              IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
                NEW.location := ST_SetSRID(
                    ST_MakePoint(NEW.longitude, NEW.latitude), 4326
                )::geography;
              END IF;
              NEW.search_doc := lower(
                coalesce(NEW.name, '') || ' ' ||
                coalesce(NEW.address, '') || ' ' ||
                coalesce(NEW.primary_type, '')
              );
              IF NEW.thumb_url IS NULL AND NEW.image_url IS NOT NULL THEN
                NEW.thumb_url := NEW.image_url;
              END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute("DROP TRIGGER IF EXISTS trg_gaming_places_discovery_touch ON gaming_places")
        op.execute(
            """
            CREATE TRIGGER trg_gaming_places_discovery_touch
            BEFORE INSERT OR UPDATE OF name, address, primary_type, latitude, longitude, image_url
            ON gaming_places
            FOR EACH ROW
            EXECUTE FUNCTION gaming_places_discovery_touch()
            """
        )
    else:
        # SQLite / non-PG: btree lat/lng only (Appendix A path)
        op.create_index(
            "ix_gaming_places_lat_lng",
            "gaming_places",
            ["latitude", "longitude"],
        )
        op.create_index(
            "ix_gaming_places_available_now",
            "gaming_places",
            ["available_now"],
        )
        op.create_index(
            "ix_gaming_places_rating_score",
            "gaming_places",
            ["rating_score", "id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute("DROP TRIGGER IF EXISTS trg_gaming_places_discovery_touch ON gaming_places")
        op.execute("DROP FUNCTION IF EXISTS gaming_places_discovery_touch()")
        op.execute("DROP INDEX IF EXISTS ix_gaming_places_amenities_mask")
        op.execute("DROP INDEX IF EXISTS ix_gaming_places_search_doc_trgm")
        op.execute("DROP INDEX IF EXISTS ix_gaming_places_rating_score")
        op.execute("DROP INDEX IF EXISTS ix_gaming_places_available_now")
        op.execute("DROP INDEX IF EXISTS ix_gaming_places_lat_lng")
        op.execute("DROP INDEX IF EXISTS ix_gaming_places_location")
        op.execute("ALTER TABLE gaming_places DROP COLUMN IF EXISTS location")
    else:
        op.drop_index("ix_gaming_places_rating_score", table_name="gaming_places")
        op.drop_index("ix_gaming_places_available_now", table_name="gaming_places")
        op.drop_index("ix_gaming_places_lat_lng", table_name="gaming_places")

    op.drop_column("gaming_places", "review_count")
    op.drop_column("gaming_places", "search_doc")
    op.drop_column("gaming_places", "thumb_url")
    op.drop_column("gaming_places", "price_paise")
    op.drop_column("gaming_places", "amenities_mask")
    op.drop_column("gaming_places", "rating_score")
    op.drop_column("gaming_places", "available_now")
