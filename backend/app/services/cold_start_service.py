"""Cold start service per ALG-BE04."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.recommendation_engine import build_personalized_feed


async def onboard_new_user(user_id: UUID, city: str | None = None, game_preferences: list[str] | None = None, db: AsyncSession | None = None):
    """Pre-seed interest profile from onboarding choices. Sets low confidence."""
    # In full: insert or update user_interest_profiles with seeded game_scores ~0.6 for chosen, confidence=0.05
    if game_preferences:
        print(f"[coldstart] seeding {user_id} with {game_preferences}")
    return {"user_id": str(user_id), "profile_confidence": 0.05}


async def build_cold_start_feed(user_id: UUID, limit: int = 20, db: AsyncSession | None = None, user_lat: float | None = None, user_lng: float | None = None):
    """Return trending + nearby + high-engagement for new users."""
    # Delegate to engine cold path
    if db is None:
        return {"items": [], "personalized": False}
    return await build_personalized_feed(db, None, user_id, "home", 1, limit, user_lat, user_lng)
