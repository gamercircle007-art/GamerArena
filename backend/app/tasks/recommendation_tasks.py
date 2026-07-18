"""Celery tasks for recommendation / algorithm brain (ALG-BE05)."""

from datetime import datetime

from app.core.config import get_settings
from app.db.session import async_session_maker  # may need adjust per project
from app.services.recommendation_engine import compute_trending, compute_user_interests
from app.tasks.celery_app import celery_app

settings = get_settings()


@celery_app.task(name="recommendation.update_user_interest_profile", bind=True, max_retries=2)
def update_user_interest_profile(self, user_id: str):
    """Upsert profile, clear user feed caches. Called for significant actions."""
    import asyncio
    from app.db.session import get_sync_session  # fallback if needed; use async in worker if configured

    # For dev simplicity we run sync-ish; in prod use proper async celery or loop
    try:
        # Placeholder: real impl would run async compute + upsert to user_interest_profiles
        # and redis DEL feed:*:{user_id}:*
        print(f"[celery] update_user_interest_profile for {user_id}")
        # TODO: full async execution inside task (requires celery async support or run_in_executor)
        return {"user_id": user_id, "status": "scheduled"}
    except Exception as exc:
        self.retry(exc=exc, countdown=30)


@celery_app.task(name="recommendation.refresh_engagement_stats")
def refresh_engagement_stats():
    print("[celery] refresh_engagement_stats (stub aggregate to content_engagement_stats)")
    return {"status": "ok"}


@celery_app.task(name="recommendation.refresh_trending_1h")
def refresh_trending_1h():
    # run sync wrapper
    import asyncio
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # In real worker with proper db injection:
        # n = loop.run_until_complete(_run_trending(1))
        print("[celery] refresh_trending_1h")
        return {"refreshed": 0}
    finally:
        loop.close()


@celery_app.task(name="recommendation.refresh_trending_6h")
def refresh_trending_6h():
    print("[celery] refresh_trending_6h")
    return {"refreshed": 0}


@celery_app.task(name="recommendation.refresh_trending_24h")
def refresh_trending_24h():
    print("[celery] refresh_trending_24h")
    return {"refreshed": 0}


@celery_app.task(name="recommendation.cleanup_old_data")
def cleanup_old_data():
    print("[celery] cleanup_old_data (impressions 30d, interactions 90d)")
    return {"status": "ok"}


@celery_app.task(name="recommendation.seed_all_interest_profiles")
def seed_all_interest_profiles():
    print("[celery] seed_all_interest_profiles (one time)")
    return {"status": "ok"}
