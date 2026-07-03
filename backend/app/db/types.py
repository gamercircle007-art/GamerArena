"""Cross-dialect column types for local SQLite dev and PostgreSQL."""

from geoalchemy2 import Geography
from sqlalchemy import JSON, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

PortableJSON = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")

PortableStringArray = JSON().with_variant(ARRAY(String(50)), "postgresql")

PortableTextArray = JSON().with_variant(ARRAY(Text()), "postgresql")

PortableGeography = String(255).with_variant(
    Geography(geometry_type="POINT", srid=4326),
    "postgresql",
)