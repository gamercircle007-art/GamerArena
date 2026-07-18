# GameConnect Algorithm Brain — PROGRESS TRACKER
# Grok: `cat PROGRESS_ALGORITHM.md` → first [ ] → build → mark [x] YYYY-MM-DD → next
# Reference: ALGORITHM_MASTER_CONTEXT.md (full scoring formula, all code samples)
# ─────────────────────────────────────────────────────────────────────────────

## PHASE 1 — DATABASE MIGRATIONS

- [x] ALG-DB01: Create migration — user_interactions table (signal collection)  (2026-07-10)
      File: `alembic revision -m "add_recommendation_user_interactions"`
      Table: user_interactions (full schema in ALGORITHM_MASTER_CONTEXT.md)
      Indexes: (user_id, created_at DESC), (content_id, action), (action, created_at DESC), session_id
      Run: `alembic upgrade head`

- [x] ALG-DB02: Create migration — user_interest_profiles table (2026-07-10, +018 migration)
- [x] ALG-DB03: Create migration — content_engagement_stats table (2026-07-10)
- [x] ALG-DB04: Create migration — trending_items + feed_impressions + search_events (2026-07-10)

---

## PHASE 2 — BACKEND MODELS + SCHEMAS

- [x] ALG-BE01: Create backend/app/models/recommendation.py + registered in db/models (2026-07-10)
- [x] ALG-BE02: Create backend/app/schemas/recommendation.py (2026-07-10)
      → TrackInteractionRequest: content_type, content_id, action, view_duration_ms?, ...
      → FeedResponse: items[], page, feed_type, personalized: bool
      → FeedItem: content_type, content_id, score, is_trending, source_label
      → TrendingResponse: items[], window, computed_at
      → SearchResponse: query, results{parlors,tournaments,users,posts}, suggestions[]
      → UserInterestResponse: game_scores{}, prefers_reels, profile_confidence
      → AlgoStatsResponse: (for admin) total_interactions, profiles_computed, trending_count
      → SearchAnalyticsResponse: top_queries[], zero_result_queries[], avg_ctr

---

## PHASE 3 — RECOMMENDATION ENGINE SERVICE

- [x] ALG-BE03: Create backend/app/services/recommendation_engine.py (full track/compute/generate/score/build/trending/smart) (2026-07-10)

      Section A — track_interaction()
        → Insert to user_interactions table
        → Update Redis counters (pipeline: content:counts:{id}, user:seen:{id})
        → Trigger Celery update_user_interest_profile if significant action

      Section B — compute_user_interests()
        → Query last 90 days of interactions with action weights
        → Compute game_scores (normalized 0-1)
        → Compute creator_scores (top 50)
        → Compute content type preferences
        → Return profile dict with confidence score

      Section C — generate_candidates()
        → Bucket 1 (30%): following posts (last 7 days)
        → Bucket 2 (30%): interest-based by top 3 game types
        → Bucket 3 (25%): trending from trending_items table
        → Bucket 4 (10%): nearby tournaments/parlors (PostGIS)
        → Bucket 5 (10%): exploration (high-engagement random)
        → Deduplicate + remove already-seen (Redis set)

      Section D — score_and_rank()
        → Load user interest profile
        → Load engagement stats (batch query)
        → For each candidate: relevance + freshness + engagement + creator_affinity + trending_bonus
        → Apply diversity_modifier (penalize 4th+ same game type)
        → Sort by final_score descending

      Section E — build_personalized_feed()
        → Check Redis cache (key: feed:{type}:{user_id}:page{n}, TTL 10min)
        → Cold start path: show trending + high-engagement if confidence < 0.1
        → Warm start: generate_candidates → score_and_rank
        → Record impressions in Redis
        → Cache result in Redis

      Section F — compute_trending()
        → SQL query: engagement velocity per content in last N hours
        → Score = (positive_actions * 2 - negative_actions * 3) / views * log(views)
        → Insert to trending_items table
        → Write Redis sorted set: trending:{window}

      Section G — smart_search()
        → PostgreSQL full-text search with ts_rank for parlors
        → ILIKE fallback for tournaments + users
        → Log SearchEvent to DB
        → Update search:popular Redis sorted set
        → Return results + autocomplete suggestions

- [x] ALG-BE04: Create backend/app/services/cold_start_service.py (2026-07-10)
- [x] ALG-BE05: Create backend/app/tasks/recommendation_tasks.py + registered (2026-07-10)
- [x] ALG-BE06: Register Celery Beat schedule in celery_app.py (2026-07-10)

---

## PHASE 5 — API ROUTERS

- [x] ALG-BE07/08/09/11: Updated routers/recommendation.py (ranked+reels+trending+discover+interactions+smart+autocomplete+stats) + main include (2026-07-10)
- [x] ALG-BE10: Basic /admin/algo/stats + /refresh-trending in recommendation router (2026-07-10)

---

- [x] ALG-FL01: visibility_detector already present + used (2026-07-10)
- [x] ALG-FL02: Created lib/features/feed/data/interaction_repository.dart (2026-07-10)
- [x] ALG-FL03: Created lib/features/feed/providers/ranked_feed_provider.dart (2026-07-10)
- [x] ALG-FL04: Created lib/shared/widgets/trackable_feed_item.dart (2026-07-10)
- [x] ALG-FL05: Wired HomeScreen + rankedFeedProvider + TrackableFeedItem demo (2026-07-10)

- [ ] ALG-FL06: Update existing ReelsScreen
      REPLACE: existing reels fetch with GET /feed/reels
      Track view_duration_ms for each reel (use VideoPlayerController.position)
      Track 'replay' when user watches again

- [ ] ALG-FL07: Update Search screen
      REPLACE: GET /search with GET /search/smart
      ADD: autocomplete as user types (GET /search/autocomplete?q=)
      ADD: trending searches section when input is empty
      Track: when user taps a search result — log clicked_content_id to search event

- [ ] ALG-FL08: Update onboarding — cold start seeding
      After role selection → show game preference picker:
        "Which games do you play?" (multi-select chips: BGMI, FIFA, Valorant, VR, etc.)
      After selection: POST /interactions/track for each chosen game with action='preference'
      → Triggers cold_start seeding

---

## PHASE 7 — ANGULAR ADMIN ALGO ANALYTICS

- [ ] ALG-AD01: Create src/pages/algo/AlgoPage (Angular: algo.component.ts)
      Tabs: Overview | Trending | User Interests | Search | Feed Quality | Cold Start
      Add to sidebar: "🧠 Algorithm" → /admin/algo

- [ ] ALG-AD02: Overview tab
      → 4 KPI cards: Active Profiles | Avg Confidence | Trending Now | Searches Today
      → Recharts AreaChart: interaction volume last 7 days (stacked by action type)
      → Mini table: top 5 trending items with scores

- [ ] ALG-AD03: Trending tab
      → Window selector buttons: [1h] [6h] [24h]
      → Recharts BarChart: top 20 content by trending_score
      → Recharts PieChart: game category distribution of trending
      → City dropdown filter
      → DataTable: rank | content | type | score | views | likes | hide_rate | actions

- [ ] ALG-AD04: User Interests tab
      → Recharts Heatmap (or grouped bar): game_type × avg_score across user base
        → "On average, 72% of users have BGMI score > 0.5"
      → Histogram: profile confidence distribution
      → Pie: content type preferences (reels/posts/tournaments split)
      → "Force recompute" button for specific user ID

- [ ] ALG-AD05: Search Analytics tab
      → Bar chart: top 20 search queries (last 24h)
      → Red/amber table: zero-result queries (searches with no results found)
      → Line chart: search volume per hour
      → CTR metric: % of searches that led to a click

- [ ] ALG-AD06: Feed Quality tab
      → Line chart: avg engagement rate per day (home vs reels vs discover)
      → "Force refresh trending" button → POST /admin/algo/refresh-trending

- [ ] ALG-AD07: Cold Start tab
      → Counter: users with confidence < 0.2 (need more data)
      → Actions: [Export list] [Trigger onboarding nudge notification]

---

## PHASE 8 — TESTING

- [ ] ALG-TEST01: Test track_interaction endpoint
      → POST 100 interactions for test user
      → Verify rows in user_interactions table
      → Verify Redis counters updated

- [ ] ALG-TEST02: Test compute_user_interests
      → Seed 50+ fake interactions for user with BGMI-heavy activity
      → Run compute_user_interests(user_id)
      → Verify game_scores["BGMI"] > 0.7

- [ ] ALG-TEST03: Test build_personalized_feed
      → Cold start user → verify gets trending content
      → Warm user → verify BGMI content ranked higher than FIFA for BGMI user
      → Verify no duplicate content_ids in one page

- [ ] ALG-TEST04: Test trending computation
      → Seed 100 interactions on one post in last 1 hour
      → Run compute_trending(window_hours=1)
      → Verify post appears in trending_items with non-zero score

- [ ] ALG-TEST05: Test smart search
      → GET /search/smart?q=BGMI
      → Verify results include parlors + tournaments with BGMI
      → Verify search_events table has new row
      → Verify Redis search:popular updated

---

## SESSION LOG
| Date | Tasks Completed | Next Task | Notes |
|------|----------------|-----------|-------|
| Day 0 | Planning | ALG-DB01 | Start with 4 migrations |
