"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "paythan",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

# Auto-discover (loads recommendation_tasks etc)
celery_app.autodiscover_tasks(["app.tasks"])

# Periodic schedule per ALGORITHM kit
celery_app.conf.beat_schedule = {
    "refresh-trending-1h": {
        "task": "recommendation.refresh_trending_1h",
        "schedule": crontab(minute="*/15"),
    },
    "refresh-trending-6h": {
        "task": "recommendation.refresh_trending_6h",
        "schedule": crontab(hour="*/1"),
    },
    "refresh-trending-24h": {
        "task": "recommendation.refresh_trending_24h",
        "schedule": crontab(hour="*/6"),
    },
    "refresh-engagement-stats": {
        "task": "recommendation.refresh_engagement_stats",
        "schedule": crontab(minute="*/15"),
    },
    "cleanup-old-data": {
        "task": "recommendation.cleanup_old_data",
        "schedule": crontab(hour=3, minute=0),
    },
    "sweep-expired-booking-holds": {
        "task": "booking.sweep_expired_holds",
        "schedule": crontab(minute="*/5"),
    },
    "nightly-booking-reconciliation": {
        "task": "booking.nightly_reconciliation",
        "schedule": crontab(hour=2, minute=15),
    },
    # Club Management occupancy analytics read these rollups exclusively — if these
    # stop running, the heatmap/utilization screens go stale rather than slow.
    "refresh-occupancy-rollups": {
        "task": "club_ops.refresh_occupancy_rollups",
        "schedule": crontab(minute=10),
    },
    "nightly-rollup-repair": {
        "task": "club_ops.nightly_rollup_repair",
        "schedule": crontab(hour=2, minute=45),
    },
    # Discovery denorm — list endpoint must never JOIN slots/reviews
    "discovery-refresh-availability": {
        "task": "discovery.refresh_availability",
        "schedule": crontab(minute="*"),
        "options": {"expires": 55},
    },
    "discovery-refresh-rating-scores": {
        "task": "discovery.refresh_rating_scores",
        "schedule": crontab(minute="*/15"),
    },
}
celery_app.conf.timezone = "Asia/Kolkata"

# Ensure discovery tasks module is imported for beat/worker
celery_app.conf.imports = list(
    set(
        list(getattr(celery_app.conf, "imports", None) or [])
        + [
            "app.tasks.discovery",
            "app.tasks.booking_tasks",
            "app.tasks.recommendation_tasks",
            "app.tasks.club_ops_tasks",
        ]
    )
)