# GameConnect — Build Progress Tracker
# Grok: Read this file at the start of EVERY session.
# Find first [ ] task → build it → mark [x] with date → move to next.
# ─────────────────────────────────────────────────────────────────────

## HOW GROK USES THIS FILE
1. Run ```cat PROGRESS.md``` to see current state
2. Find first unchecked `[ ]` task
3. Build it completely (files + packages + migration if needed)  
4. Mark it `[x] DONE YYYY-MM-DD`
5. Continue to next task
6. Update SESSION LOG at bottom when done for the day

---

## PHASE 0 — Foundation ← ALREADY DONE (your existing project)
- [x] P0-B01: Backend folder structure
- [x] P0-B02: config.py with environment variables
- [x] P0-B03: main.py — FastAPI app + CORS + routers
- [x] P0-B04: models/base.py — SQLAlchemy async engine
- [x] P0-B05: User model (id, phone, email, name, avatar_url, role, fcm_token, is_active)
- [x] P0-B06: Parlor model (id, owner_id, name, description, logo_url, address, location GEOGRAPHY, game_types, is_verified, follower_count)
- [x] P0-B07: Alembic setup + initial migration (users + parlors tables)
- [x] P0-B08: docker-compose.yml (fastapi + postgis + redis)
- [x] P0-A01: Auth schemas (SendOtpRequest, VerifyOtpRequest, TokenResponse)
- [x] P0-A02: auth_service.py (OTP generation, Redis storage, JWT create/verify)
- [x] P0-A03: routers/auth.py (send-otp, verify-otp, google, refresh, logout)
- [x] P0-A04: deps.py (get_db, get_redis, get_current_user)
- [x] P0-U01: schemas/user.py (UserCreate, UserUpdate, UserResponse)
- [x] P0-U02: routers/users.py (GET/PUT /users/me, GET /users/{id})
- [x] P0-P01: schemas/parlor.py (ParlorCreate, ParlorUpdate, ParlorResponse)
- [x] P0-P02: routers/parlors.py (POST/GET/PUT /parlors)
- [x] P0-F01: Flutter project created (parlour_app)
- [x] P0-F02: pubspec.yaml dependencies added
- [x] P0-F03: app_config.dart + app_theme.dart
- [x] P0-F04: dio_client.dart with JWT interceptor
- [x] P0-F05: app_router.dart with go_router + auth guard
- [x] P0-F06: auth_provider.dart (Riverpod)
- [x] P0-FA01: login_screen.dart
- [x] P0-FA02: otp_screen.dart
- [x] P0-FA03: role_picker_screen.dart
- [x] P0-FA04: auth_repository.dart

---

## PHASE 1 — REMAINING BACKEND (Build these next)

### Missing DB Models + Migration
- [x] P1-DB01: Add missing models: Post, Comment, Like, Follow, Tournament, Booking, Notification — DONE 2026-06-27
      → Created domain models: parlor, post, comment, like, follow, tournament (+booking), notification
      → Extended User with role, avatar_url, fcm_token
      → Migration: `005_add_social_tournament_tables.py` (run `alembic upgrade head` with PostGIS Postgres)
      → docker-compose postgres image updated to postgis/postgis:16-3.4-alpine

- [x] P1-DB02: Add PostGIS GIST index on parlors.location — DONE 2026-06-27
      → Migration `006_add_gist_index_parlors_location.py`

### Tournament Module
- [x] P1-T01: Create schemas/tournament.py — DONE 2026-06-27
      → TournamentCreate, TournamentUpdate, TournamentResponse with nested ParlorSummary

- [x] P1-T02: Create routers/tournaments.py — DONE 2026-06-27
      → POST/GET/PUT/DELETE /tournaments + GET /parlors/{id}/tournaments
      → repository, service, parlor router wired in main.py

### Booking Module (CRITICAL — use Redis lock pattern)
- [x] P1-BK01: Create services/booking_service.py — DONE 2026-06-27
      → book_slot with Redis SETNX lock + SELECT FOR UPDATE
      → cancel_booking (>2hr before start, decrements booked_slots)

- [x] P1-BK02: Create schemas/booking.py — DONE 2026-06-27
      → BookingResponse (id, tournament_id, user_id, slot_number, status, payment_status, created_at)

- [x] P1-BK03: Create routers/bookings.py — DONE 2026-06-27
      → POST /tournaments/{id}/book, DELETE /bookings/{id}
      → GET /tournaments/{id}/bookings (owner), GET /users/me/bookings

### Post Module
- [ ] P1-PS01: Create schemas/post.py
      → PostCreate (content, media_urls[], tournament_id optional)
      → PostResponse (id, content, media_urls, parlor{id,name,logo_url,is_verified}, tournament{id,title} optional, likes_count, comments_count, is_liked bool, created_at)

- [ ] P1-PS02: Create routers/posts.py
      → POST /posts (owner only)
      → GET /posts/{id} (public, include is_liked if authenticated)
      → DELETE /posts/{id} (owner only, cascade delete comments+likes)
      → Also add: PUT /parlors/{id}/posts GET endpoint to parlors router

### Feed Module
- [ ] P1-FD01: Create services/feed_service.py
      → build_feed(user_id, page, limit, db, redis, user_lat, user_lng)
      → Query: posts from parlors user follows + nearby top open tournaments
      → Redis cache key: `feed:{user_id}:{page}`, TTL 60s
      → Cache invalidation: called from posts router on POST /posts

- [ ] P1-FD02: Create routers/feed.py
      → GET /feed?page=1&limit=20 (user only)
      → Returns mixed list: posts + tournament_announcement items

### Comments Module
- [ ] P1-C01: Create schemas/comment.py
      → CommentCreate (content, parent_id optional)
      → CommentResponse (id, user{id,name,avatar_url}, content, parent_id, likes_count, is_liked, is_deleted, created_at, reply_count)

- [ ] P1-C02: Create routers/comments.py
      → GET /posts/{id}/comments?limit=20&after_id={cursor}&sort=oldest
         (only top-level: WHERE parent_id IS NULL)
      → POST /posts/{id}/comments (user, body: {content, parent_id?})
         increment post.comments_count
      → GET /comments/{id}/replies?limit=10&page=1
      → DELETE /comments/{id} — soft delete (is_deleted=True), only own comment OR parlor owner on their post
      → POST /comments/{id}/like — toggle like

### Likes Module
- [ ] P1-LK01: Create routers/likes.py
      → POST /likes body:{target_type:'post'|'comment', target_id:uuid}
         Use INSERT ... ON CONFLICT DO NOTHING, increment likes_count
      → DELETE /likes/{target_type}/{target_id}
         Decrement likes_count

### Follows Module
- [ ] P1-FL01: Create routers/follows.py
      → POST /follows body:{parlor_id} — insert follow, increment parlor.follower_count
      → DELETE /follows/{parlor_id} — delete follow, decrement follower_count
      → GET /users/me/following — list followed parlors
      → Also update GET /parlors/{id} to include is_following:bool if authenticated

### Geo Module
- [ ] P1-GE01: Create services/geo_service.py
      → nearby_parlors(lat, lng, radius_m, game_type, limit, db)
         SQL: `ST_DWithin(location, ST_MakePoint(:lng,:lat)::geography, :radius)`
         Returns: parlors + distance_meters field
      → nearby_tournaments(lat, lng, radius_m, status, db)
         JOIN tournaments ON parlors via ST_DWithin

- [ ] P1-GE02: Create routers/geo.py
      → GET /geo/nearby-parlors?lat=28.6&lng=77.2&radius=5000&game_type=BGMI&limit=20
      → GET /geo/nearby-tournaments?lat=&lng=&radius=&status=open&date_from=

### Search Module
- [ ] P1-SR01: Create routers/search.py
      → GET /search?q=BGMI&type=all|parlor|tournament&limit=20
      → Use ILIKE for parlor name/description search
      → Use ILIKE for tournament title/game_type search
      → Return unified results: [{type:'parlor'|'tournament', data:{...}}]

### Notifications Module
- [ ] P1-NF01: Create services/notification_service.py
      → create_notification(user_id, type, title, body, data_dict, db)
      → Called by: booking_service (booking_confirmed), follows (new_follower), posts (new_post)

- [ ] P1-NF02: Create routers/notifications.py
      → GET /notifications?is_read=false&limit=30
      → PUT /notifications/{id}/read
      → PUT /notifications/read-all
      → GET /notifications/unread-count (for badge in app)

### Analytics
- [ ] P1-AN01: Add GET /parlors/me/analytics to parlors router
      → Returns: follower_count, total_posts, upcoming_tournaments_count,
                 total_bookings_this_month, bookings_by_tournament[]

### Uploads Module
- [ ] P1-UP01: Create routers/uploads.py
      → POST /uploads/presigned-url body:{file_type:'image/jpeg', purpose:'post_media'}
      → Use boto3: s3.generate_presigned_url('put_object', ...)
      → Returns: {upload_url (PUT to S3 directly), public_url (CloudFront)}
      → Install: pip install boto3

---

## PHASE 1 — REMAINING FLUTTER (Build after backend is ready)

### Shared Models
- [ ] P1-FM01: Create shared/models/ — all Dart model classes
      → user.dart, parlor.dart, post.dart, comment.dart, tournament.dart, booking.dart, notification.dart
      → Each has: fromJson(), toJson(), copyWith()
      → Use json_serializable OR write manually

### Shared Widgets
- [ ] P1-FW01: shared/widgets/tournament_card.dart
      → Shows: game type icon, title, parlor name, date, slots left badge (green/red), entry fee, Book button
      → Props: Tournament tournament, VoidCallback onTap, VoidCallback onBook

- [ ] P1-FW02: shared/widgets/post_card.dart
      → Shows: parlor avatar + name + verified badge, post text, image (CachedNetworkImage), like/comment/share row
      → Like button: optimistic toggle + count update
      → Props: Post post, VoidCallback onLike, VoidCallback onComment

- [ ] P1-FW03: shared/widgets/slot_selector.dart
      → GridView of slots: green=open, red=booked, blue=mine
      → Animated color transition when slot is booked (for real-time WS updates)
      → Props: int totalSlots, int bookedSlots, int? mySlotNumber

- [ ] P1-FW04: shared/widgets/user_avatar.dart + verified_badge.dart
      → CachedNetworkImage avatar with fallback initials
      → Verified badge: small purple checkmark icon overlay

- [ ] P1-FW05: shared/widgets/loading_shimmer.dart
      → Shimmer loading card (use shimmer package)
      → PostCardShimmer, TournamentCardShimmer variants

### Core Flutter Files (if missing)
- [ ] P1-FC01: core/providers/location_provider.dart
      → Use geolocator to get current GPS position
      → RequestPermission → getCurrentPosition
      → Expose: AsyncValue<Position> currentPosition

- [ ] P1-FC02: Check ws_service.dart exists — if not, create core/network/ws_service.dart
      → Singleton WebSocket connection with auto-reconnect (exponential backoff: 1s→2s→4s→8s)
      → subscribe(channel), unsubscribe(channel), events stream
      → Reconnect on disconnect: re-subscribe all active channels

### Feature Screens
- [ ] P1-FS01: features/feed/providers/feed_provider.dart
      → AsyncNotifier fetching GET /feed?page=1
      → InfiniteScroll: fetchNextPage()
      → addPostToTop(Post) for WS new_post event

- [ ] P1-FS02: features/feed/presentation/feed_screen.dart
      → ListView with PostCard + TournamentCard items
      → InfiniteScrollPagination (use infinite_scroll_pagination package)
      → Pull-to-refresh
      → "N new posts ↑" banner when WS pushes new_post

- [ ] P1-FS03: features/tournament/providers/tournament_provider.dart
      → AsyncNotifier fetching GET /tournaments/{id}
      → updateSlots(int bookedSlots) — called by WS slot_booked event

- [ ] P1-FS04: features/tournament/providers/booking_provider.dart
      → bookSlot(tournamentId) → POST /tournaments/{id}/book
      → Optimistic: set isBooking=true → API call → success/fail state
      → On success: update tournament slot count locally

- [ ] P1-FS05: features/tournament/presentation/tournament_detail_screen.dart
      → Hero image, title, parlor info, stats row
      → SlotSelector widget (updates live via WS)
      → "Book Slot" CTA button (disabled when full, spinner when booking)
      → Prize accordion + Rules expandable
      → Comments preview (first 5) + "See all" → CommentsScreen

- [ ] P1-FS06: features/tournament/presentation/create_tournament_screen.dart (owner only)
      → Form: title, game_type dropdown, format dropdown, date/time pickers
      → total_slots, entry_fee (0 = free), prizes (1st/2nd/3rd text fields), rules textarea
      → Submit → POST /tournaments

- [ ] P1-FS07: features/comments/providers/comments_provider.dart
      → AsyncNotifier for post comments
      → loadComments(postId) → GET /posts/{id}/comments
      → addCommentOptimistic(content, parentId?) — local insert first, then API
      → toggleLike(commentId) — optimistic like toggle
      → WS: subscribe to post:comments:{postId}, handle new_comment event

- [ ] P1-FS08: features/comments/presentation/comments_screen.dart
      → Post preview at top (collapsed)
      → Paginated comment list (CommentTile widgets)
      → Threaded replies: indent + "View N more replies" lazy load toggle
      → Sticky input bar at bottom (TextField + Send button)
      → Replying to: "@username" chip appears above input with X cancel

- [ ] P1-FS09: features/map/presentation/discover_screen.dart
      → flutter_map with TileLayer (OpenStreetMap)
      → Custom markers for parlors (pulse if live tournament)
      → Bottom sheet on marker tap: parlor name, game types, distance, "View Profile" button
      → Toggle: Map View ↔ List View
      → Filter bar: Game type chips, Distance radius slider

- [ ] P1-FS10: features/parlor/presentation/parlor_profile_screen.dart
      → Cover + logo, name, verified badge, address, game types chips
      → Follower count + Follow/Unfollow button
      → Tabs: Posts (grid) | Tournaments (list)
      → Each tab lazy-loads from /parlors/{id}/posts and /parlors/{id}/tournaments

- [ ] P1-FS11: features/parlor/presentation/owner_dashboard_screen.dart (owner only)
      → Stats cards: followers, posts this week, upcoming tournaments, total bookings
      → My Tournaments list (status badges: Open/Full/Live/Completed)
        Tap tournament → see attendees list
      → My Posts grid (like/comment counts)
      → FAB: + New Post / + New Tournament

- [ ] P1-FS12: features/profile/presentation/user_profile_screen.dart
      → Avatar, name, join date, edit profile button
      → Followed parlors horizontal scroll
      → Upcoming bookings preview

- [ ] P1-FS13: features/profile/presentation/my_bookings_screen.dart
      → Tabs: Upcoming | Past
      → Each booking: tournament name, parlor, date, slot number, status badge

- [ ] P1-FS14: features/notifications/presentation/notifications_screen.dart
      → Grouped by date (Today / Yesterday / Older)
      → Each item: type icon, title, body, timestamp, unread dot
      → Tap → deep link to tournament/post/parlor
      → Swipe to dismiss (mark read)

- [ ] P1-FS15: Create Post screen (owner only)
      → TextField for content
      → Image picker (image_picker) → upload via /uploads/presigned-url → S3 direct upload
      → Optional: link to tournament (search dropdown)
      → Submit → POST /posts

- [ ] P1-FS16: Connect all screens to real backend (replace any mock/hardcoded data)
      → Update app_router.dart with all routes
      → Test complete user journey: Login → Feed → Find Tournament → Book Slot → See Booking

---

## PHASE 2 — REAL-TIME (After Phase 1 works end-to-end)

### WebSocket Backend
- [ ] P2-WS01: app/ws/manager.py — ConnectionManager with Redis pub/sub
      → connect(ws, user_id), disconnect(user_id), subscribe(user_id, channel)
      → broadcast_to_channel(channel, payload) — publishes to Redis `ws:{channel}`
      → redis_listener() background task — reads Redis pub/sub → forwards to WS clients

- [ ] P2-WS02: app/ws/router.py — FastAPI WS endpoint
      → `ws://api/ws?token={jwt}` — verify JWT on connect
      → Handle client messages: {action:'subscribe'|'unsubscribe', channel:str}
      → Handle ping/pong keepalive
      → On disconnect: cleanup from connection map + subscriptions

- [ ] P2-WS03: Integrate WS into booking_service.py
      → After successful booking: await publish_event(redis, f"tournament:{tournament_id}", slot_booked_payload)

- [ ] P2-WS04: Integrate WS into posts router
      → After POST /posts: fan-out new_post event to all followers of that parlor via Redis pub/sub

- [ ] P2-WS05: Integrate WS into comments router
      → After POST comment: publish new_comment event to post:comments:{post_id} channel

- [ ] P2-WS06: Integrate WS into notification_service
      → After create_notification: publish notification event to user:{user_id} channel

### Flutter WebSocket Integration
- [ ] P2-FW01: Update tournament_provider.dart — subscribe tournament:{id} on screen enter, unsubscribe on exit
      → Handle slot_booked event → call updateSlots()

- [ ] P2-FW02: Update comments_provider.dart — subscribe post:comments:{postId}
      → Handle new_comment event → insert at bottom of list

- [ ] P2-FW03: Update feed_provider.dart — subscribe user:{userId}
      → Handle new_post event → insert at top, show "1 new post ↑" banner

- [ ] P2-FW04: Global notification WS listener in main.dart / auth_provider
      → Handle notification event → increment unread badge, show snackbar

### Redis Caching
- [ ] P2-RC01: feed_service.py: cache feed per user (TTL 60s), invalidate on new post
- [ ] P2-RC02: GET /tournaments/{id}: cache tournament (TTL 30s), invalidate on booking
- [ ] P2-RC03: Geo queries: cache with rounded lat/lng key (TTL 120s)
- [ ] P2-RC04: GET /notifications/unread-count: cache per user (TTL 30s)

### Celery
- [ ] P2-CE01: app/tasks/celery_app.py — Celery setup with Redis broker
- [ ] P2-CE02: Task: send_fcm_push(user_id, title, body, data) — use firebase-admin
      pip install firebase-admin
- [ ] P2-CE03: Call Celery task from notification_service.py (async background)

---

## PHASE 3 — PAID + SCALE (Future)
- [ ] P3-01: Razorpay payment for tournament entry fees
- [ ] P3-02: Tournament group chat (WS rooms per tournament)
- [ ] P3-03: Direct messaging
- [ ] P3-04: Admin panel
- [ ] P3-05: Flutter Web support

---

## SESSION LOG
| Date | Tasks Completed | Next Task | Notes |
|------|----------------|-----------|-------|
| Day 1 | Phase 0 (existing project) | P1-DB01 | Auth + setup already done |
| 2026-06-27 | P1-DB01 (all social/tournament DB models + migration 005) | P1-DB02 | Parlor model was missing from repo; added as prerequisite. Run migration via `docker compose up` then `alembic upgrade head` |
| 2026-06-27 | P1-DB02, P1-T01, P1-T02 (GIST index + tournament module) | P1-BK01 | UserResponse extended with role/avatar_url. Run `alembic upgrade head` when Postgres is up |
| 2026-06-27 | P1-BK01, P1-BK02, P1-BK03 (booking module + Redis lock) | P1-PS01 | booking/domain: service, repository, schemas, router |
