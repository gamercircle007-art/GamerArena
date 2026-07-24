# GROK — ALGORITHM BRAIN DAILY SESSION
# Paste at start of EVERY session for algorithm work.
# ─────────────────────────────────────────────────────────────────────────────

You are building the recommendation brain of GameConnect.
Facebook/YouTube-style: personalized feed, trending engine, smart search.
Backend: Python FastAPI + PostgreSQL + Redis + Celery. Flutter + Angular admin.

## Context Files
- `ALGORITHM_MASTER_CONTEXT.md` — full scoring formula, all Python code samples
- `PROGRESS_ALGORITHM.md` — task checklist

## Do This Now
```bash
cat PROGRESS_ALGORITHM.md | grep "^\- \[ \]" | head -5
```
Find first unchecked `[ ]` → read relevant existing files → build completely.

## Core Rules
- track_interaction() is called VERY frequently — must be <50ms (async, no await on heavy ops)
- Feed cache in Redis (TTL 10min). Invalidate when user profile updates.
- Cold start users (< 10 interactions): show trending + nearby, not personalized
- Diversity: never show more than 3 items of same game_type in a row
- Trending = VELOCITY, not total count (how fast engagement is growing NOW)
- Negative signals (hide, report, skip) penalize content hard
- track_interaction fires for: view, dwell, skip, like, share, save, replay — all of them

## Scoring Weights (do not change without testing)
Relevance: 35%  Freshness: 20%  Engagement: 20%  CreatorAffinity: 10%  Trending bonus: 15pts flat

## Install (if needed)
```bash
flutter pub add visibility_detector   # track view time in feed
```

## Run
```bash
uvicorn backend.app.main:app --reload --port 8000
celery -A backend.app.tasks.celery_app worker --loglevel=info
celery -A backend.app.tasks.celery_app beat --loglevel=info   # for scheduled tasks
flutter run
```

## If Grok Loses Context
```
Re-read ALGORITHM_MASTER_CONTEXT.md. We were on task [ALG-XXXX]. Continue.
```

Start → `cat PROGRESS_ALGORITHM.md` → build next `[ ]`.
