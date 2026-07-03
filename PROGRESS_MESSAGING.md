# GameConnect — Messaging + Social PROGRESS TRACKER
# Backend: Python FastAPI (domain-driven) | Frontend: Flutter 3.x + Riverpod
# Completed: 2026-06-29

---

## PHASE 1 — DATABASE MIGRATIONS

- [x] M-DB01–M-DB05: Combined in `backend/alembic/versions/009_add_messaging_social_tables.py`
      Tables: friend_requests, friendships, user_blocks, stories, story_views,
      user_locations, user_profiles, close_friends, extended messages/conversations, user_last_seen

---

## PHASE 2 — BACKEND MODELS + SCHEMAS

- [x] M-BE01: `backend/app/domains/friend/models.py`
- [x] M-BE02: `backend/app/domains/story/models.py`
- [x] M-BE03: `backend/app/domains/snap_map/models.py`
- [x] M-BE04: `backend/app/domains/messaging/models.py`
- [x] M-BE05: Schemas in each domain (`friend/`, `story/`, `snap_map/`, `messaging/`, `online/`)

---

## PHASE 3 — BACKEND SERVICES

- [x] M-BE06: `backend/app/domains/online/service.py`
- [x] M-BE07: `backend/app/domains/friend/service.py`
- [x] M-BE08: `backend/app/domains/story/service.py`
- [x] M-BE09: `backend/app/domains/snap_map/service.py`
- [x] M-BE10: `backend/app/domains/messaging/service.py` (incl. mark_delivered, ephemeral celery)
- [x] M-BE11: `backend/app/ws/router.py`

---

## PHASE 4 — BACKEND ROUTERS

- [x] M-BE12: `backend/app/domains/friend/router.py` + block endpoints in `user/router.py`
- [x] M-BE13: `backend/app/domains/story/router.py`
- [x] M-BE14–M-BE15: `backend/app/domains/snap_map/router.py` + `online/router.py`
- [x] M-BE16: `backend/app/domains/messaging/router.py`
- [x] M-BE17: `backend/app/tasks/story_cleanup.py`, `ephemeral_messages.py`
- [x] M-BE18: Registered in `backend/app/main.py`

---

## PHASE 5 — FLUTTER MODELS + REPOSITORIES

- [x] M-FL01: `lib/shared/models/` (message, conversation, friendship, story, online_status, user_profile, user_location, snap_map_user)
- [x] M-FL02: `lib/features/friends/data/friends_repository.dart`
- [x] M-FL03: `lib/features/stories/data/stories_repository.dart`
- [x] M-FL04: `lib/features/snap_map/data/location_repository.dart`
- [x] M-FL05: `lib/features/profile/data/profile_repository.dart`

---

## PHASE 6 — FLUTTER PROVIDERS

- [x] M-FL06: `lib/features/friends/providers/friends_provider.dart`
- [x] M-FL07: `lib/features/stories/providers/stories_provider.dart` (incl. myStoriesProvider)
- [x] M-FL08: `lib/features/snap_map/providers/snap_map_provider.dart`
- [x] M-FL09: `lib/features/messaging/providers/conversations_provider.dart`
- [x] M-FL10: `lib/features/messaging/providers/messages_provider.dart`

---

## PHASE 7 — FLUTTER SHARED WIDGETS

- [x] M-FL11: `lib/shared/widgets/online_dot.dart`
- [x] M-FL12: `lib/shared/widgets/stories_avatar_ring.dart`
- [x] M-FL13: `lib/shared/widgets/message_bubble.dart`
- [x] M-FL14: `lib/shared/widgets/typing_indicator.dart`
- [x] M-FL15: `lib/shared/widgets/reactions_row.dart`
- [x] M-FL16: `lib/shared/widgets/map_user_marker.dart`

---

## PHASE 8 — FLUTTER SCREENS

- [x] M-FL17: `conversations_screen.dart` (my story header, search, online dots)
- [x] M-FL18: `chat_screen.dart` (attachments, emoji, date separators, ephemeral, typing)
- [x] M-FL19: `stories_rail.dart`
- [x] M-FL20: `story_viewer.dart`
- [x] M-FL21: `story_creator.dart`
- [x] M-FL22: `snap_map_screen.dart`
- [x] M-FL23: `friend_requests_screen.dart`
- [x] M-FL24: `find_friends_screen.dart`
- [x] M-FL25: `public_profile_screen.dart`
- [x] M-FL26: `my_profile_screen.dart` (QR, edit, privacy link)

---

## PHASE 9 — INTEGRATION

- [x] M-FL27: StoriesRail + map in FeedScreen
- [x] M-FL28: Snapchat-style center camera FAB in `main_shell_scaffold.dart`
- [x] M-FL29: `SocialTopBarActions` in Feed + Conversations app bars
- [x] M-FL30: `UserAvatar` with story ring + online dot + profile tap
- [x] M-FL31: `ws_service.dart` heartbeat + online users map
- [x] M-FL32: `ws_connection_provider.dart` connects on auth

---

## PHASE 10 — ONLINE STATUS

- [x] M-FL33: End-to-end online status (backend WS + Flutter providers + UI dots)
- [x] M-FL33 UI: `friends_list_screen.dart` added

---

## PHASE 11 — PUSH NOTIFICATIONS (FCM)

- [x] M-FL34: Stub `lib/core/services/push_notification_service.dart` (wire Firebase when credentials added)
- [x] M-FL35: Backend FCM via `notification/service.py` → `tasks/push.py` stub + Celery queue
- [x] M-FL36: `ws_listener.dart` deep-link routing for message/friend/story notifications

---

## PHASE 12 — PRIVACY SETTINGS

- [x] M-FL37: `privacy_settings_screen.dart` (incl. Stories privacy section)

---

## SESSION LOG
| Date | Tasks Completed | Notes |
|------|----------------|-------|
| 2026-06-29 | All M-DB01 through M-FL37 | Full Snapchat-style messaging + social system integrated into gamer-circle |