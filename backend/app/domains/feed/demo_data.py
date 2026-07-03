"""Load demo feed / store payloads from JSON files."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.domains.feed.schemas import FeedResponse

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


@lru_cache
def _read_json(name: str) -> dict:
    path = _DATA_DIR / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_demo_feed() -> FeedResponse:
    """Return the static demo feed for local development."""
    return FeedResponse.model_validate(_read_json("demo_feed.json"))


def load_demo_store() -> dict:
    """Return demo store catalog."""
    return _read_json("demo_store.json")