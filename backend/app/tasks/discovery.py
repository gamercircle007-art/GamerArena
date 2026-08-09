"""Discovery Celery jobs — denormalize availability + Bayesian ratings.

Reads stay cheap: list endpoint never JOINs slots/bookings/reviews.
"""

from __future__ import annotations

import time

from sqlalchemy import text

from app.db.session import async_session_factory
from app.tasks.celery_app import celery_app

# Bayesian prior: pull sparse 5.0s below well-reviewed 4.6s
BAYES_C = 4.0  # prior mean
BAYES_M = 10.0  # prior weight (pseudo-reviews)


def _run_async(coro):
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


async def _refresh_availability_async() -> dict:
    """Single set-based UPDATE; only touch changed rows."""
    sql = text(
        """
        WITH computed AS (
            SELECT
                gp.id,
                EXISTS (
                    SELECT 1
                    FROM gaming_slots s
                    WHERE s.parlour_id = gp.id
                      AND s.slot_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::date
                      AND s.is_available = true
                      AND s.start_time <= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::time
                      AND s.end_time   >  (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Kolkata')::time
                      AND s.current_bookings < s.max_players
                ) AS avail
            FROM gaming_places gp
        )
        UPDATE gaming_places gp
        SET available_now = c.avail
        FROM computed c
        WHERE gp.id = c.id
          AND gp.available_now IS DISTINCT FROM c.avail
        """
    )
    async with async_session_factory()() as session:
        result = await session.execute(sql)
        await session.commit()
        return {"rows_changed": result.rowcount}


async def _refresh_rating_scores_async() -> dict:
    """Bayesian average in one UPDATE ... FROM."""
    sql = text(
        """
        WITH stats AS (
            SELECT
                gaming_place_id AS id,
                AVG(rating)::float AS r,
                COUNT(*)::int AS v
            FROM parlour_ratings
            GROUP BY 1
        ),
        computed AS (
            SELECT
                gp.id,
                CASE
                    WHEN s.v IS NULL OR s.v = 0 THEN coalesce(gp.rating, 0)
                    ELSE ((:m * :c) + (s.r * s.v)) / (:m + s.v)
                END AS score,
                coalesce(s.v, coalesce(gp.user_ratings_total, 0)) AS reviews
            FROM gaming_places gp
            LEFT JOIN stats s ON s.id = gp.id
        )
        UPDATE gaming_places gp
        SET rating_score = c.score,
            review_count = c.reviews
        FROM computed c
        WHERE gp.id = c.id
          AND (
            gp.rating_score IS DISTINCT FROM c.score
            OR gp.review_count IS DISTINCT FROM c.reviews
          )
        """
    )
    async with async_session_factory()() as session:
        result = await session.execute(sql, {"c": BAYES_C, "m": BAYES_M})
        await session.commit()
        return {"rows_changed": result.rowcount}


async def _refresh_search_docs_async() -> dict:
    """Backfill search_doc (trigger keeps it current on writes)."""
    sql = text(
        """
        UPDATE gaming_places
        SET search_doc = lower(
            coalesce(name, '') || ' ' ||
            coalesce(address, '') || ' ' ||
            coalesce(primary_type, '')
        )
        WHERE search_doc IS DISTINCT FROM lower(
            coalesce(name, '') || ' ' ||
            coalesce(address, '') || ' ' ||
            coalesce(primary_type, '')
        )
        """
    )
    async with async_session_factory()() as session:
        result = await session.execute(sql)
        await session.commit()
        return {"rows_changed": result.rowcount}


@celery_app.task(
    name="discovery.refresh_availability",
    acks_late=False,
    expires=55,
    ignore_result=True,
)
def refresh_availability() -> dict:
    t0 = time.perf_counter()
    out = _run_async(_refresh_availability_async())
    ms = (time.perf_counter() - t0) * 1000
    print(f"[celery] discovery.refresh_availability {out} in {ms:.1f}ms")
    return {**out, "ms": round(ms, 1)}


@celery_app.task(
    name="discovery.refresh_rating_scores",
    ignore_result=True,
)
def refresh_rating_scores() -> dict:
    t0 = time.perf_counter()
    out = _run_async(_refresh_rating_scores_async())
    ms = (time.perf_counter() - t0) * 1000
    print(f"[celery] discovery.refresh_rating_scores {out} in {ms:.1f}ms")
    return {**out, "ms": round(ms, 1)}


@celery_app.task(
    name="discovery.refresh_search_docs",
    ignore_result=True,
)
def refresh_search_docs() -> dict:
    t0 = time.perf_counter()
    out = _run_async(_refresh_search_docs_async())
    ms = (time.perf_counter() - t0) * 1000
    print(f"[celery] discovery.refresh_search_docs {out} in {ms:.1f}ms")
    return {**out, "ms": round(ms, 1)}
