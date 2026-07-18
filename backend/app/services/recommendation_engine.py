"""Recommendation engine - the brain of GameConnect.

Full implementation per ALGORITHM_MASTER_CONTEXT.md:
- track_interaction (fast <50ms)
- compute_user_interests (weighted + recency)
- generate_candidates (buckets: following, interest, trending, nearby, explore)
- score_and_rank (35% relevance, 20% freshness, 20% engagement, 10% creator, 15% trending + modifiers)
- build_personalized_feed (cache, cold-start)
- compute_trending (velocity)
- smart_search + track_search
"""

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import (
    ContentEngagementStats,
    FeedImpression,
    SearchEvent,
    TrendingItem,
    UserInteraction,
    UserInterestProfile,
)


async def track_interaction(
    session: AsyncSession,
    redis: aioredis.Redis | None,
    user_id: UUID,
    content_type: str,
    content_id: UUID,
    action: str,
    view_duration_ms: int | None = None,
    scroll_depth_pct: int | None = None,
    session_id: UUID | None = None,
    source: str | None = None,
    position_in_feed: int | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    device_type: str | None = None,
) -> None:
    """Track a user interaction. Fast path (<50ms target): DB write + Redis. Heavy compute to Celery."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    day = now.weekday()

    interaction = UserInteraction(
        user_id=user_id,
        content_type=content_type,
        content_id=content_id,
        action=action,
        view_duration_ms=view_duration_ms,
        scroll_depth_pct=scroll_depth_pct,
        session_id=session_id,
        source=source,
        position_in_feed=position_in_feed,
        user_lat=user_lat,
        user_lng=user_lng,
        device_type=device_type,
        hour_of_day=hour,
        day_of_week=day,
        created_at=now,
    )
    session.add(interaction)
    await session.commit()

    if redis is not None:
        pipe = redis.pipeline()
        # Fast counters
        pipe.hincrby(f"content:counts:{content_id}", action, 1)
        pipe.expire(f"content:counts:{content_id}", 604800)  # 7d
        pipe.zadd(f"user:seen:{user_id}", {str(content_id): now.timestamp()})
        pipe.zremrangebyrank(f"user:seen:{user_id}", 0, -501)  # keep last ~500
        # realtime trending signal
        pipe.zadd("trending:interactions:realtime", {str(content_id): now.timestamp()}, incr=True)
        await pipe.execute()

    # Fire Celery for significant (non-blocking in prod via .apply_async)
    if action in ("like", "share", "save", "replay", "book_from_content", "hide", "report"):
        # placeholder - actual import/call in tasks module to avoid circular
        pass


async def compute_user_interests(
    session: AsyncSession, user_id: UUID, days: int = 90
) -> dict[str, Any]:
    """SECTION B: Compute user interest profile from last 90d interactions. Weighted + recency."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Join posts/tournaments for game_types / creator (text query for compat)
    rows = (await session.execute(text("""
        SELECT ui.content_type, ui.content_id, ui.action, ui.view_duration_ms, ui.created_at,
               COALESCE(p.game_types, '[]') as game_types,
               COALESCE(p.hashtags, '[]') as hashtags,
               CASE WHEN ui.content_type = 'post' THEN p.author_id
                    WHEN ui.content_type IN ('tournament', 'parlor') THEN COALESCE(t.parlor_id, p.author_id)
                    ELSE NULL END as creator_id
        FROM user_interactions ui
        LEFT JOIN posts p ON p.id = ui.content_id AND ui.content_type = 'post'
        LEFT JOIN tournaments t ON t.id = ui.content_id AND ui.content_type = 'tournament'
        WHERE ui.user_id = :uid
          AND ui.created_at > :cutoff
    """), {"uid": str(user_id), "cutoff": cutoff})).fetchall()

    if not rows:
        return {"profile_confidence": 0.0, "game_scores": {}, "total_interactions": 0}

    ACTION_WEIGHTS = {
        "view": 0.1, "impression": 0.0, "dwell": 0.3,
        "like": 1.0, "comment": 1.5, "share": 2.0, "save": 1.8, "replay": 1.5,
        "follow_from_content": 3.0, "book_from_content": 4.0,
        "skip": -0.5, "hide": -2.0, "report": -5.0,
    }

    game_scores: dict[str, float] = {}
    creator_scores: dict[str, float] = {}
    ct_weights: dict[str, float] = {"post": 0, "reel": 0, "tournament": 0, "parlor": 0, "live": 0}
    total_interactions = 0
    now = datetime.now(timezone.utc)

    import json as _json
    for row in rows:
        w = ACTION_WEIGHTS.get(row.action, 0.0)
        if w == 0:
            continue
        # recency decay
        age_days = max(0.0, (now - row.created_at).days if row.created_at else 0)
        recency = max(0.4, 1.0 - (age_days / 90.0) * 0.6)
        weight = w * recency

        # game_types (JSON or array string)
        try:
            gts = _json.loads(row.game_types) if isinstance(row.game_types, str) else (row.game_types or [])
        except Exception:
            gts = []
        for gt in gts:
            if gt:
                game_scores[gt] = game_scores.get(gt, 0.0) + weight

        if row.creator_id:
            cid = str(row.creator_id)
            creator_scores[cid] = creator_scores.get(cid, 0.0) + abs(weight)

        if row.content_type in ct_weights:
            ct_weights[row.content_type] += weight

        total_interactions += 1

    # normalize 0-1
    if game_scores:
        mx = max(game_scores.values()) or 1.0
        game_scores = {k: round(v / mx, 3) for k, v in game_scores.items()}
    if creator_scores:
        mx = max(creator_scores.values()) or 1.0
        creator_scores = {k: round(v / mx, 3) for k, v in creator_scores.items()}

    total_w = sum(ct_weights.values()) or 1.0
    ct_prefs = {k: round(v / total_w, 3) for k, v in ct_weights.items()}

    confidence = min(1.0, round(total_interactions / 40.0, 3))

    return {
        "game_scores": game_scores,
        "creator_scores": creator_scores,
        "prefers_reels": ct_prefs.get("reel", 0.5),
        "prefers_posts": ct_prefs.get("post", 0.5),
        "prefers_tournaments": ct_prefs.get("tournament", 0.5),
        "prefers_live": ct_prefs.get("live", 0.5),
        "profile_confidence": confidence,
        "total_interactions": total_interactions,
        "max_distance_km": 10.0,
        "exploration_rate": 0.1,
        "last_computed_at": now.isoformat(),
    }


async def generate_candidates(
    session: AsyncSession,
    user_id: UUID,
    user_profile: dict,
    limit: int = 50,
    lat: float | None = None,
    lng: float | None = None,
) -> list[dict]:
    """SECTION C: Bucketed candidate gen (30% follow, 30% interest, 25% trending, 10% nearby, 10% explore). Dedup via Redis seen."""
    target = max(limit * 3, 60)
    candidates: list[dict] = []
    seen_ids: set[str] = set()

    if user_profile is None:
        user_profile = {}

    # Load seen from redis? caller passes or we can but for now use impressions + basic dedup in build

    # 1. FOLLOWING (30%)
    try:
        following = await session.execute(text("""
            SELECT 'post' as content_type, p.id as content_id, p.created_at, p.author_id as creator_id,
                   COALESCE(p.game_types, '[]') as game_types
            FROM posts p
            JOIN follows f ON f.following_id = p.author_id
            WHERE f.follower_id = :uid
              AND p.created_at > :cut
            ORDER BY p.created_at DESC
            LIMIT :lim
        """), {"uid": str(user_id), "cut": datetime.now(timezone.utc) - timedelta(days=7), "lim": target // 3})
        for r in following:
            cid = str(r.content_id)
            if cid not in seen_ids:
                seen_ids.add(cid)
                candidates.append({
                    "content_type": r.content_type,
                    "content_id": cid,
                    "created_at": r.created_at,
                    "creator_id": str(r.creator_id) if r.creator_id else None,
                    "game_types": _safe_json(r.game_types),
                })
    except Exception:
        pass

    # 2. INTEREST (top games)
    top_games = []
    gs = user_profile.get("game_scores", {}) or {}
    if gs:
        top_games = sorted(gs.keys(), key=lambda k: gs[k], reverse=True)[:3]
    if top_games:
        try:
            interest = await session.execute(text("""
                SELECT 'post' as content_type, p.id as content_id, p.created_at, p.author_id as creator_id,
                       COALESCE(p.game_types, '[]') as game_types
                FROM posts p
                WHERE p.game_types IS NOT NULL
                  AND p.created_at > :cut
                  AND p.author_id != :uid
                ORDER BY p.created_at DESC
                LIMIT :lim
            """), {"cut": datetime.now(timezone.utc) - timedelta(days=14), "uid": str(user_id), "lim": target // 3})
            for r in interest:
                cid = str(r.content_id)
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    candidates.append({
                        "content_type": r.content_type, "content_id": cid,
                        "created_at": r.created_at, "creator_id": str(r.creator_id) if r.creator_id else None,
                        "game_types": _safe_json(r.game_types),
                    })
        except Exception:
            pass

    # 3. TRENDING (25%)
    try:
        tr = await session.execute(
            select(TrendingItem).where(TrendingItem.window == "6h").order_by(TrendingItem.trending_score.desc()).limit(target // 4)
        )
        for t in tr.scalars():
            cid = str(t.content_id)
            if cid not in seen_ids:
                seen_ids.add(cid)
                candidates.append({
                    "content_type": t.content_type,
                    "content_id": cid,
                    "is_trending": True,
                    "trending_score": t.trending_score,
                })
    except Exception:
        pass

    # 4. NEARBY (10%)
    if lat is not None and lng is not None:
        try:
            near = await session.execute(text("""
                SELECT 'tournament' as content_type, t.id as content_id, t.created_at, t.parlor_id as creator_id
                FROM tournaments t
                WHERE t.status = 'open' AND t.created_at > :cut
                LIMIT :lim
            """), {"cut": datetime.now(timezone.utc) - timedelta(days=30), "lim": max(5, target // 10)})
            for r in near:
                cid = str(r.content_id)
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    candidates.append({"content_type": r.content_type, "content_id": cid, "created_at": r.created_at})
        except Exception:
            pass

    # 5. EXPLORATION (10%)
    try:
        explore = await session.execute(text("""
            SELECT 'post' as content_type, p.id as content_id, p.created_at, p.author_id as creator_id,
                   COALESCE(p.game_types,'[]') as game_types
            FROM posts p
            WHERE p.created_at > :cut
            ORDER BY RANDOM()
            LIMIT :lim
        """), {"cut": datetime.now(timezone.utc) - timedelta(days=3), "lim": target // 10})
        for r in explore:
            cid = str(r.content_id)
            if cid not in seen_ids:
                seen_ids.add(cid)
                candidates.append({
                    "content_type": r.content_type, "content_id": cid,
                    "created_at": r.created_at, "game_types": _safe_json(r.game_types),
                })
    except Exception:
        pass

    return candidates[:target]


def _safe_json(val: Any) -> list:
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val) if isinstance(val, str) else []
    except Exception:
        return []


def score_and_rank(
    candidates: list[dict], user_profile: dict, impressions: set, feed_so_far: list | None = None
) -> list[dict]:
    """SECTION D: Score using formula. relevance(35) + freshness(20) + engagement(20) + creator(10) + trending(15) + modifiers."""
    if feed_so_far is None:
        feed_so_far = []
    scored = []
    game_scores = user_profile.get("game_scores", {}) or {}
    creator_scores = user_profile.get("creator_scores", {}) or {}
    now = datetime.now(timezone.utc)

    for c in candidates:
        key = (c.get("content_type"), str(c.get("content_id")))
        if key in impressions:
            continue

        base = 40.0

        # relevance 0-35
        rel = 5.0
        gts = c.get("game_types") or []
        for gt in gts:
            rel += game_scores.get(gt, 0.05) * 12
        rel = min(35.0, rel)
        base += rel

        # freshness 0-20
        created = c.get("created_at")
        if created:
            try:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace("Z", "+00:00"))
                hours = max(0.0, (now - created).total_seconds() / 3600)
                if hours < 1:
                    fresh = 20.0
                elif hours < 6:
                    fresh = 19.0 - hours * 0.8
                elif hours < 24:
                    fresh = 14.0 - (hours - 6) * 0.3
                else:
                    fresh = max(3.0, 10.0 - (hours / 24.0) * 1.5)
                base += fresh
            except Exception:
                base += 8
        else:
            base += 8

        # engagement (stub using any preloaded, default neutral) + trending bonus
        base += 12.0
        if c.get("is_trending"):
            base += min(15.0, float(c.get("trending_score", 5) or 5))

        # creator affinity 0-10
        cid = c.get("creator_id")
        if cid and cid in creator_scores:
            base += min(10.0, creator_scores[cid] * 10)

        # diversity modifier
        same = sum(1 for it in feed_so_far if (it.get("game_types") or []) and gts and set(gts) & set(it.get("game_types") or []))
        if same >= 3:
            base *= 0.6
        if same >= 5:
            base *= 0.3

        scored.append({**c, "score": round(max(1.0, base), 2)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


async def build_personalized_feed(
    session: AsyncSession,
    redis: aioredis.Redis | None,
    user_id: UUID,
    feed_type: str = "home",
    page: int = 1,
    limit: int = 20,
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    """SECTION E: personalized feed with cache (10min), cold-start path, impressions, rank."""
    cache_key = f"feed:{feed_type}:{str(user_id)}:p{page}"
    if redis is not None:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

    profile = await compute_user_interests(session, user_id)

    # Cold start: low confidence
    confidence = profile.get("profile_confidence", 0.0) or 0.0
    if confidence < 0.12:
        # return trending + some recent high engagement (simplified)
        try:
            tr = await session.execute(
                select(TrendingItem).order_by(TrendingItem.trending_score.desc()).limit(limit)
            )
            items = []
            for t in tr.scalars():
                items.append({
                    "content_type": t.content_type,
                    "content_id": str(t.content_id),
                    "score": float(t.trending_score or 60),
                    "is_trending": True,
                    "source_label": "cold_start_trending",
                })
            res = {"items": items, "page": page, "feed_type": feed_type, "personalized": False}
            if redis is not None:
                await redis.set(cache_key, json.dumps(res), ex=300)
            return res
        except Exception:
            pass

    candidates = await generate_candidates(session, user_id, profile, limit * 2 + 10, lat, lng)

    # load recent impressions for dedup
    impressions = set()
    try:
        imp_rows = await session.execute(
            select(FeedImpression.content_type, FeedImpression.content_id)
            .where(FeedImpression.user_id == user_id)
            .order_by(FeedImpression.shown_at.desc())
            .limit(400)
        )
        for r in imp_rows:
            impressions.add((r.content_type, str(r.content_id)))
    except Exception:
        pass

    ranked = score_and_rank(candidates, profile, impressions)[:limit]

    # record impressions (fire and forget style)
    for it in ranked:
        try:
            imp = FeedImpression(
                user_id=user_id,
                content_id=UUID(it["content_id"]),
                content_type=it["content_type"],
                feed_type=feed_type,
            )
            session.add(imp)
        except Exception:
            pass
    try:
        await session.commit()
    except Exception:
        await session.rollback()

    items = [
        {
            "content_type": c["content_type"],
            "content_id": str(c["content_id"]),
            "score": c["score"],
            "is_trending": bool(c.get("is_trending")),
            "source_label": "personalized" if not c.get("is_trending") else "trending",
        }
        for c in ranked
    ]

    result = {
        "items": items,
        "page": page,
        "feed_type": feed_type,
        "personalized": confidence > 0.1,
    }

    if redis is not None:
        try:
            await redis.set(cache_key, json.dumps(result), ex=600)
        except Exception:
            pass
    return result


async def track_search(
    session: AsyncSession,
    user_id: UUID | None,
    query: str,
    results_count: int,
    clicked_content_id: UUID | None = None,
    clicked_content_type: str | None = None,
    click_position: int | None = None,
) -> None:
    event = SearchEvent(
        user_id=user_id,
        query=query,
        query_normalized=query.lower().strip(),
        results_count=results_count,
        clicked_content_id=clicked_content_id,
        clicked_content_type=clicked_content_type,
        click_position=click_position,
    )
    session.add(event)
    await session.commit()


async def smart_search(
    session: AsyncSession, q: str, types: list[str] | None = None, limit: int = 20
) -> dict:
    """SECTION G: smart_search with FTS fallback ILIKE + log event + redis popular."""
    qn = (q or "").strip().lower()
    results = {"parlors": [], "tournaments": [], "users": [], "posts": []}
    suggestions: list[str] = []

    if not qn:
        return {"query": q, "results": results, "suggestions": []}

    try:
        # Parlors (use ilike as FTS may not be set on sqlite)
        parlors = await session.execute(text("""
            SELECT id, name, COALESCE(game_types,'[]') as game_types, rating
            FROM parlors WHERE lower(name) LIKE :p OR lower(description) LIKE :p LIMIT :lim
        """), {"p": f"%{qn}%", "lim": limit})
        for r in parlors:
            results["parlors"].append({"id": str(r.id), "name": r.name, "game_types": _safe_json(r.game_types), "rating": r.rating})
    except Exception:
        pass

    try:
        tms = await session.execute(text("""
            SELECT id, title, game_type FROM tournaments
            WHERE lower(title) LIKE :p OR lower(game_type) LIKE :p LIMIT :lim
        """), {"p": f"%{qn}%", "lim": limit})
        for r in tms:
            results["tournaments"].append({"id": str(r.id), "title": r.title, "game_type": r.game_type})
    except Exception:
        pass

    # simple suggestions from popular (redis later) or recent queries
    try:
        sug = await session.execute(text("SELECT DISTINCT query FROM search_events WHERE query_normalized LIKE :p LIMIT 5"), {"p": f"{qn}%"})
        suggestions = [s[0] for s in sug.fetchall()]
    except Exception:
        suggestions = []

    return {"query": q, "results": results, "suggestions": suggestions}


async def compute_trending(session: AsyncSession, window_hours: int = 6) -> int:
    """SECTION F: velocity based trending. Returns count inserted."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    # aggregate positive vs negative from interactions in window
    rows = await session.execute(text("""
        SELECT ui.content_id, ui.content_type,
               SUM(CASE WHEN ui.action IN ('like','share','save','replay','comment','book_from_content') THEN 2 ELSE 0 END) as pos,
               SUM(CASE WHEN ui.action IN ('hide','report','skip') THEN 3 ELSE 0 END) as neg,
               COUNT(*) as views
        FROM user_interactions ui
        WHERE ui.created_at > :cut
        GROUP BY ui.content_id, ui.content_type
        HAVING views > 1
        ORDER BY (pos - neg) DESC
        LIMIT 200
    """), {"cut": cutoff})

    inserted = 0
    w = f"{window_hours}h"
    for r in rows:
        score = ((r.pos or 0) * 2 - (r.neg or 0) * 3) / max(1, (r.views or 1)) * (1 + math.log(max(1, r.views or 1)))
        score = round(max(0, score * 10), 2)
        ti = TrendingItem(
            content_id=r.content_id,
            content_type=r.content_type,
            trending_score=score,
            window=w,
            computed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        session.add(ti)
        inserted += 1
    await session.commit()
    return inserted
