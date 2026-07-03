# DMS — Document Management System PROGRESS TRACKER
# Grok: `cat PROGRESS_DMS.md` → first [ ] → build completely → mark [x] YYYY-MM-DD → next
# Reference: DMS_MASTER_CONTEXT.md for full specs, schemas, code samples
# Touches: Flutter app + Python backend + Angular admin panel
# ─────────────────────────────────────────────────────────────────────────────

## DAILY USAGE
Start: "Read DMS_MASTER_CONTEXT.md and PROGRESS_DMS.md. Build next unchecked task."
End:   "Mark done [x] with date. Update SESSION LOG."

---

## PHASE 1 — DATABASE MIGRATION

- [x] DMS-DB01: Create migration — media_assets table (CORE) — 2026-07-03
      File: `alembic revision -m "create_media_assets_table"`
      Table: media_assets (full schema in DMS_MASTER_CONTEXT.md)
      ALL indexes: uploader_id, context+context_id, asset_type, status, created_at
      Run: `alembic upgrade head`
      Verify: `SELECT * FROM media_assets LIMIT 0;` shows all columns

- [x] DMS-DB02: Create migration — add asset_id columns to existing tables — 2026-07-03
      File: `alembic revision -m "add_asset_id_to_existing_tables"`
      ADD COLUMNS (from DMS_MASTER_CONTEXT.md ALTER TABLE section):
        users.avatar_asset_id
        parlors.logo_asset_id, parlors.cover_asset_id
        post_media.asset_id (or posts if post_media doesn't exist)
        stories.asset_id
        messages.asset_id
        ratings.review_asset_ids UUID[]
        tournaments.cover_asset_id
        parlour_events.cover_asset_id
        community_posts.asset_ids UUID[]
        parlour_gallery.asset_id
      Run: `alembic upgrade head`
      NOTE: Keep old URL columns — do NOT drop them yet

---

## PHASE 2 — BACKEND MODEL + SCHEMAS

- [x] DMS-BE01: Create backend/app/domains/dms/models.py — 2026-07-03
      → MediaAsset SQLAlchemy model (all columns from schema)
      → Add relationship: MediaAsset.uploader → User
      → Add @property: is_image, is_video, is_document, is_audio

- [x] DMS-BE02: Create backend/app/domains/dms/schemas.py — 2026-07-03
      → UploadIntentRequest: file_type, file_name, file_size, asset_type, context, context_id?
      → UploadIntentResponse: asset_id, upload_url, cdn_url
      → ConfirmUploadRequest: asset_id, width_px?, height_px?, duration_seconds?
      → ConfirmUploadResponse: asset_id, cdn_url, thumbnail_url?, status
      → AssetResponse: all MediaAsset fields + uploader name
      → AdminAssetItem: for admin listing (uploader_name, context label)
      → DmsStatsResponse: total_count, total_size_bytes, by_type:{}, by_context:{}
      → Use model_config = ConfigDict(from_attributes=True)

---

## PHASE 3 — BACKEND DMS SERVICE

- [x] DMS-BE03: Create backend/app/domains/dms/service.py — 2026-07-03
      IMPLEMENT these functions (code in DMS_MASTER_CONTEXT.md):
      → create_upload_intent(uploader_id, file_type, file_name, file_size, asset_type, context, context_id, db)
         - Validates MIME type allowed for asset_type
         - Validates file_size within limits (image 15MB, video 500MB, doc 25MB)
         - Generates UUID, builds s3_key = media/{type}/{id[:2]}/{id}.ext
         - Calls boto3 generate_presigned_url('put_object', ..., ExpiresIn=900)
         - Inserts MediaAsset with status='processing'
         - Returns {asset_id, upload_url, cdn_url}
      → confirm_upload(asset_id, uploader_id, width_px, height_px, duration_seconds, db)
         - Finds asset WHERE status='processing' AND uploader_id matches
         - Calls s3.head_object() to verify file exists in S3
         - Updates status='active', stores dimensions/duration
         - For videos: queues thumbnail Celery task
         - Returns {asset_id, cdn_url, thumbnail_url, status}
      → get_asset(asset_id, db) → MediaAsset or 404
      → soft_delete_asset(asset_id, requester_id, db) → sets status='deleted', deleted_at=now
      → update_context(asset_id, context_id, db) → updates context_id after entity creation
      → list_assets(filters, db) → paginated query with filters

- [x] DMS-BE04: Create backend/app/tasks/media_tasks.py (Celery) — 2026-07-03
      → generate_video_thumbnail(asset_id, video_cdn_url) Celery task:
         - Download video from CDN URL
         - Use ffmpeg to extract frame at 1 second mark
         - Upload thumbnail to S3: media/thumbnails/{asset_id}_thumb.jpg
         - UPDATE media_assets SET thumbnail_url = cdn_thumb_url WHERE id = asset_id
         Requires: pip install ffmpeg-python (add to requirements.txt)

---

## PHASE 4 — BACKEND DMS ROUTERS

- [x] DMS-BE05: Create backend/app/domains/dms/router.py — 2026-07-03
      ENDPOINTS:
      → POST /dms/upload-intent         → calls dms_service.create_upload_intent()
      → POST /dms/confirm-upload        → calls dms_service.confirm_upload()
      → GET  /dms/assets/{id}           → calls dms_service.get_asset()
      → DELETE /dms/assets/{id}         → calls dms_service.soft_delete_asset()
      → PATCH /dms/assets/{id}/context  → body:{context_id} → update context
      → GET  /dms/assets                → ?context=&context_id=&type=&page=&limit=20
         Rate limit: 60 requests per minute per user
      All routes: require authenticated user

- [x] DMS-BE06: Create backend/app/domains/dms/admin_router.py — 2026-07-03
      ENDPOINTS (all require admin role):
      → GET  /admin/dms
         ?type=&context=&uploader_id=&is_flagged=&status=&date_from=&date_to=&search=&page=&limit=
         → Returns PaginatedResponse<AdminAssetItem>
      → GET  /admin/dms/stats
         → total assets, total bytes, breakdown by type, breakdown by context
      → GET  /admin/dms/orphans
         → assets WHERE context_id IS NULL AND created_at < NOW() - INTERVAL '24 hours' AND status='active'
      → DELETE /admin/dms/{id}    → HARD delete: remove from S3 + delete from DB
      → PATCH /admin/dms/{id}/flag  body:{is_flagged:bool, reason?:str}
      → PATCH /admin/dms/{id}/status  body:{status:'active'|'deleted'|'flagged'}
      → POST /admin/dms/bulk-delete  body:{asset_ids:[]}
         → Loop: hard delete each from S3 + DB

- [x] DMS-BE07: Register DMS routers in backend/app/main.py — 2026-07-03
      → from .routers import dms, admin_dms
      → app.include_router(dms.router, prefix="/v1", tags=["DMS"])
      → app.include_router(admin_dms.router, prefix="/v1", tags=["Admin DMS"])
      → REMOVE or DEPRECATE: existing /uploads/presigned-url endpoint
         (keep it working but redirect to /dms/upload-intent internally)

---

## PHASE 5 — FLUTTER CORE DMS LAYER

- [x] DMS-FL01: Add file_picker to pubspec.yaml — 2026-07-03
      ```bash
      flutter pub add file_picker
      ```

- [x] DMS-FL02: Create lib/shared/models/media_asset.dart — 2026-07-03
      → MediaAsset class: id, uploaderID, cdnUrl, thumbnailUrl, assetType, fileType,
                         fileSizeBytes, fileSizeLabel, context, contextId, widthPx, heightPx,
                         durationSeconds, status, createdAt
      → fromJson(), toJson()
      → bool get isImage, isVideo, isDocument, isAudio

- [x] DMS-FL03: Create lib/core/services/dms_service.dart — 2026-07-03
      IMPLEMENT (full code in DMS_MASTER_CONTEXT.md):
      → uploadFile({file, assetType, fileType, context, contextId, onProgress}) → DmsUploadResult
         Three steps: uploadIntent → PUT to S3 → confirmUpload
      → getAsset(assetId) → MediaAsset
      → deleteAsset(assetId) → void
      → updateContext(assetId, contextId) → void
      → Expose as dmsServiceProvider (Riverpod Provider)

- [x] DMS-FL04: Create lib/shared/widgets/dms_upload_widget.dart — 2026-07-03
      IMPLEMENT (full code in DMS_MASTER_CONTEXT.md):
      → DmsUploadWidget with props: context, allowedTypes, onUploaded, existingCdnUrl, etc.
      → Internal states: empty, uploading (with CircularProgressIndicator + %), preview
      → _EmptyState: icon + "Tap to upload {type}" text
      → _UploadingState: progress indicator + percent
      → _PreviewState: image preview with remove (×) button
      → Picks file via ImagePicker (image/video) or FilePicker (documents)

- [ ] DMS-FL05: Create lib/shared/widgets/dms_multi_upload_widget.dart
      → List of DmsUploadWidget instances (up to maxFiles, default 10)
      → Add new row button (+ Add more)
      → Reorder support (flutter_slidable long-press drag)
      → Returns: List<DmsUploadResult>
      → Used by: CreatePostScreen, ParlourGalleryScreen

- [x] DMS-FL06: Create lib/shared/widgets/dms_media_viewer.dart — 2026-07-03
      → Shows image OR video OR document based on assetType
      → Image: CachedNetworkImage, tap → fullscreen PhotoView
      → Video: video_player package with controls, thumbnail as poster
      → Document: WebView or "Open in browser" link for PDFs
      → Audio: audioplayers with waveform + play/pause button
      → Used everywhere: PostDetailScreen, ChatScreen, ReviewPhotos, StoryViewer

---

## PHASE 6 — REPLACE EXISTING UPLOAD FLOWS

- [ ] DMS-FL07: Update EditProfileScreen / Avatar upload
      FIND: existing avatar S3 upload code
      REPLACE WITH: DmsUploadWidget(context:'user_avatar', allowedTypes:['image'], ...)
      AFTER UPLOAD: ref.read(profileProvider.notifier).updateAvatar(assetId, cdnUrl)
      BACKEND: PUT /users/me/profile now accepts {avatar_asset_id} instead of {avatar_url}

- [ ] DMS-FL08: Update CreatePostScreen / Post media upload
      FIND: existing post media upload (presigned-url or direct S3)
      REPLACE WITH: DmsMultiUploadWidget(context:'post_media', allowedTypes:['image','video'])
      AFTER UPLOAD: POST /posts body includes {media_asset_ids:[id1,id2,...]}
      BACKEND: posts router stores asset_ids in post_media table

- [x] DMS-FL09: Update StoryCreatorScreen / Story media upload — 2026-07-03
      FIND: existing story upload code
      REPLACE WITH: DmsUploadWidget(context:'story', allowedTypes:['image','video'])
      AFTER UPLOAD: POST /stories body includes {asset_id: result.assetId}

- [ ] DMS-FL10: Update ChatScreen / Message media send
      FIND: existing file attachment in chat
      REPLACE WITH: DmsUploadWidget shown in attachment sheet (context:'message', allowedTypes:['image','video','document'])
      AFTER UPLOAD: send message with {asset_id, message_type: assetType}
      DmsMediaViewer shows received media in bubbles (image → inline, video → thumbnail+play, doc → file card)

- [ ] DMS-FL11: Update ParlourSettingsScreen / Parlor logo + cover upload
      FIND: parlor logo upload code
      REPLACE: Two DmsUploadWidgets (logo: context:'parlor_logo', cover: context:'parlor_cover')
      BACKEND: PUT /parlors/{id} accepts {logo_asset_id, cover_asset_id}

- [ ] DMS-FL12: Update ParlourGalleryManageScreen / Gallery photos
      FIND: parlor gallery upload
      REPLACE WITH: DmsMultiUploadWidget(context:'parlor_gallery', contextId:parlorId, allowedTypes:['image'])
      Each item stored as: POST /parlors/me/gallery {asset_id}

- [ ] DMS-FL13: Update CreateTournamentScreen / Tournament cover
      REPLACE: DmsUploadWidget(context:'tournament_cover', allowedTypes:['image'])
      BACKEND: POST /tournaments body includes {cover_asset_id}

- [ ] DMS-FL14: Update RatingScreen / Review photos
      REPLACE: DmsMultiUploadWidget(context:'review_photo', allowedTypes:['image'], maxFiles:3)
      BACKEND: POST /parlors/{id}/reviews body includes {review_asset_ids:[]}

- [ ] DMS-FL15: Update CommunityCreatePostScreen
      REPLACE: DmsMultiUploadWidget(context:'community_post', allowedTypes:['image','video'])
      BACKEND: POST /community body includes {asset_ids:[]}

---

## PHASE 7 — DISPLAY: Replace URL strings with DmsMediaViewer

- [ ] DMS-FL16: Update PostCard widget
      OLD: CachedNetworkImage(imageUrl: post.mediaUrls[0])
      NEW: DmsMediaViewer(assetId: post.postMedia[0].assetId, cdnUrl: post.postMedia[0].cdnUrl)
      NOTE: cdnUrl is in media_assets table joined with post_media — no extra API call needed

- [ ] DMS-FL17: Update MessageBubble widget
      OLD: CachedNetworkImage for image messages
      NEW: DmsMediaViewer(assetId: msg.assetId, assetType: msg.messageType, cdnUrl: msg.cdnUrl)
      → image → inline thumbnail
      → video → thumbnail + play overlay
      → document → 📄 card with filename + size + "Open" button

- [ ] DMS-FL18: Update StoryViewer widget
      OLD: direct image URL
      NEW: use story.cdnUrl (from media_assets join) + DmsMediaViewer for video stories

- [ ] DMS-FL19: Update all UserAvatar / ParlourAvatar widgets
      OLD: CachedNetworkImage(imageUrl: user.avatarUrl)
      NEW: CachedNetworkImage(imageUrl: user.avatarCdnUrl)
           NOTE: avatarCdnUrl comes from JOIN with media_assets on avatar_asset_id
                 Falls back to user.avatarUrl if avatar_asset_id is null (backward compat)

---

## PHASE 8 — ANGULAR ADMIN DMS PAGE

- [x] DMS-AD01: Create Angular admin DMS page component — 2026-07-03
      File: src/pages/dms/DmsPage (Angular: dms.component.ts)
      OR for React-style admin: src/pages/dms/DmsPage.tsx

      LAYOUT:
        Left: FilterPanel (asset type, context dropdown, status, date range, uploader search)
        Right: StatsRow + ViewToggle + [Grid/List] of asset cards

      STATS ROW (5 cards):
        Total Assets | Total Storage (e.g. 4.2 GB) | Images | Videos | Documents

      GRID VIEW (4 col):
        Each asset card:
          - Thumbnail (image) or icon (video=🎥, doc=📄, audio=🔊)
          - Type badge (color: image=cyan, video=purple, doc=amber, audio=green)
          - Filename (truncated 20 chars)
          - Size label (2.4 MB)
          - Context chip (post_media, user_avatar, etc.)
          - Uploader name + date
          - Action buttons: [👁 View full] [🚩 Flag] [🗑 Delete]

      LIST VIEW (DataTable):
        Thumb | Filename | Type | Size | Context | Uploader | Date | Status | Actions

- [ ] DMS-AD02: Create DMS Stats sub-page (/admin/dms/stats)
      → Donut chart (Recharts/ng2-charts): storage by type
      → Area chart: uploads per day (30d)
      → Table: top uploaders by storage
      → Table: uploads by context
      → [Export CSV] button

- [ ] DMS-AD03: Create Orphaned Assets sub-page (/admin/dms/orphans)
      → DataTable: filename, size, type, uploader, uploaded_at
      → [Delete] per row
      → [Delete All Orphans] button with count warning

- [x] DMS-AD04: Add DMS to Angular admin sidebar navigation — 2026-07-03
      → Add nav item: "📁 Media Library" → /admin/dms
      → Sub-items: All Assets | Stats | Orphans

- [x] DMS-AD05: Add DMS to admin API service — 2026-07-03
      → getDmsAssets(params) → GET /admin/dms
      → getDmsStats() → GET /admin/dms/stats
      → getDmsOrphans() → GET /admin/dms/orphans
      → hardDeleteAsset(id) → DELETE /admin/dms/{id}
      → flagAsset(id, reason) → PATCH /admin/dms/{id}/flag
      → bulkDelete(ids[]) → POST /admin/dms/bulk-delete

- [ ] DMS-AD06: Add DMS stats to main Admin Dashboard (existing dashboard screen)
      ADD to dashboard KPI row:
        → "Media Storage" stat card: total size used (e.g. "4.2 GB")
        → "Flagged Media" stat card: count of is_flagged=true assets
      ADD to dashboard: "Recent Uploads" section (last 5 media assets with thumbnails)

---

## PHASE 9 — CLEANUP + TESTING

- [ ] DMS-CL01: Remove deprecated /uploads/presigned-url endpoint (or mark as deprecated with note)
      Keep backward compat: make it internally call DMS service with context='legacy'

- [ ] DMS-CL02: Write migration script for existing URLs → create media_asset records
      File: backend/app/scripts/migrate_urls_to_dms.py
      → SELECT all users WHERE avatar_url IS NOT NULL AND avatar_asset_id IS NULL
         → For each: create MediaAsset with cdn_url=avatar_url, status='active', context='user_avatar'
         → UPDATE users SET avatar_asset_id = new_asset.id
      → Repeat for parlors.logo_url, post_media.media_url, etc.
      Run once: `python -m backend.app.scripts.migrate_urls_to_dms`

- [ ] DMS-CL03: Test full upload flow (unit test)
      → POST /dms/upload-intent → validate response has asset_id + upload_url
      → Mock S3 PUT → POST /dms/confirm-upload → validate status='active'
      → GET /dms/assets/{id} → validate cdn_url accessible
      File: backend/tests/test_dms.py

- [ ] DMS-CL04: Test Flutter DmsUploadWidget
      → Pick image → upload → verify progress bar → verify preview shows
      → Pick video → upload → verify thumbnail appears after confirm
      → Pick document → upload → verify file card shows in chat

- [ ] DMS-CL05: Test admin DMS page
      → Load /admin/dms → verify grid shows assets
      → Filter by type=image → verify only images shown
      → Flag an asset → verify flag badge appears
      → Delete an asset → verify removed from S3 + DB

- [ ] DMS-CL06: Verify all existing upload flows work through DMS
      → Create post with image → check media_assets table has new row
      → Send message with video → check messages.asset_id is set
      → Update avatar → check users.avatar_asset_id is set
      → All context fields properly set in media_assets

---

## SESSION LOG
| Date | Tasks Completed | Next Task | Notes |
|------|----------------|-----------|-------|
| Day 0 | Planning | DMS-DB01 | Start with DB schema |
| 2026-07-03 | DMS-DB01–BE07, FL01–FL04, FL06, FL09, AD01, AD04–AD05 | DMS-FL05, FL07–FL08 | Core DMS foundation built |
