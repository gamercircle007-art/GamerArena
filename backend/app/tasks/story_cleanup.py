"""Celery task to expire old stories."""

import asyncio

from app.db.session import get_session_factory
from app.domains.story.service import StoryService
from app.tasks.celery_app import celery_app


@celery_app.task(name="expire_stories")
def expire_stories() -> int:
    async def _run() -> int:
        async with get_session_factory()() as session:
            return await StoryService(session).expire_stories()

    return asyncio.run(_run())


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs) -> None:
    sender.add_periodic_task(300.0, expire_stories.s(), name="expire stories every 5 min")