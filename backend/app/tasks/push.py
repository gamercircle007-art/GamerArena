"""FCM push notification Celery task (stub without firebase credentials)."""

from app.tasks.celery_app import celery_app


@celery_app.task(name="send_fcm_push")
def send_fcm_push(user_id: str, title: str, body: str, data: dict | None = None) -> dict[str, str]:
    """Send FCM push. Wire firebase-admin when credentials are configured."""
    _ = (user_id, title, body, data)
    return {"status": "queued_stub"}