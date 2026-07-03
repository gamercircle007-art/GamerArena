"""Celery task to delete ephemeral messages after view."""

import asyncio
from uuid import UUID

from sqlalchemy import update

from app.db.session import get_session_factory
from app.domains.messaging.models import Message
from app.tasks.celery_app import celery_app


@celery_app.task(name="delete_ephemeral_message")
def delete_ephemeral_message(message_id: str) -> None:
    async def _run() -> None:
        async with get_session_factory()() as session:
            await session.execute(
                update(Message)
                .where(Message.id == UUID(message_id))
                .values(is_deleted=True)
            )
            await session.commit()

    asyncio.run(_run())