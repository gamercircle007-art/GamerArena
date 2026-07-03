"""Demo store catalog — served from JSON in local development."""

from fastapi import APIRouter

from app.domains.feed.demo_data import load_demo_store

router = APIRouter(prefix="/store", tags=["Store"])


@router.get("")
async def get_store_catalog() -> dict:
    """Return demo store items from ``data/demo_store.json``."""
    return load_demo_store()