# DMS — DOCUMENT MANAGEMENT SYSTEM — MASTER CONTEXT
# Centralized media store: every image, video, document in the app goes through DMS.
# Other modules only store a media_asset_id. The DMS resolves it to a CDN URL.
# Read this + PROGRESS_DMS.md every session.
# ─────────────────────────────────────────────────────────────────────────────

## WHAT WE'RE BUILDING
A single, centralized DMS (Document Management System) that:
1. Is the ONLY place media files are uploaded and stored (S3 + CloudFront)
2. Tags every asset with context (who uploaded it, what feature it belongs to)
3. Gives every asset a UUID — all other tables reference this ID, never raw URLs
4. Provides an Admin media library (browse, filter, flag, delete, orphan detection)
5. Works across the ENTIRE app: posts, avatars, stories, messages, reviews, parlors, etc.

---

## ARCHITECTURE

```
Flutter App / Admin Panel
        │
        ▼
POST /dms/upload-intent      ← App requests upload slot
        │                       Returns: {asset_id, presigned_upload_url}
        ▼
PUT directly to S3           ← App uploads file DIRECTLY to S3 (no backend bandwidth)
        │
        ▼
POST /dms/confirm-upload     ← App tells DMS: "upload done"
        │                       DMS: stores metadata, queues thumbnail generation
        ▼
        {asset_id, cdn_url, thumbnail_url}
        │
        ▼
Stored in DB as:  post.cover_asset_id = asset_id
                  user.avatar_asset_id = asset_id
                  story.asset_id = asset_id
                  message.asset_id = asset_id
                  etc.

GET /dms/assets/{id}         ← Resolve asset_id → {cdn_url, type, size, ...}
                                (used when displaying — most cdn_urls are cached in DB)
```

---

## DATABASE SCHEMA

```sql
-- ═══ CORE: MEDIA ASSETS TABLE ═══
-- THE single source of truth for ALL media in the app
CREATE TABLE media_assets (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  uploader_id       UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,

  -- File metadata
  original_filename VARCHAR(500),
  file_type         VARCHAR(100),    -- MIME: image/jpeg, video/mp4, application/pdf, audio/mpeg
  asset_type        VARCHAR(20),     -- image | video | document | audio
  file_size_bytes   BIGINT,
  file_size_label   VARCHAR(20),     -- "2.4 MB" (pre-computed for display)

  -- S3 / CDN
  s3_key            VARCHAR(1000) NOT NULL,
  s3_bucket         VARCHAR(100) NOT NULL,
  cdn_url           VARCHAR(1000) NOT NULL,  -- CloudFront URL (serve THIS)
  thumbnail_url     VARCHAR(1000),           -- Auto-generated for video/pdf
  blurhash          VARCHAR(100),            -- Low-res placeholder for images

  -- Dimensions / duration
  width_px          INT,
  height_px         INT,
  duration_seconds  FLOAT,           -- For video and audio

  -- Context tagging — where this asset is used
  context           VARCHAR(50),
  -- 'user_avatar' | 'parlor_logo' | 'parlor_cover' | 'parlor_gallery'
  -- 'post_media' | 'story' | 'message' | 'review_photo'
  -- 'tournament_cover' | 'event_cover' | 'offer_image' | 'community_post'
  context_id        UUID,            -- ID of the related entity (if known at upload time)

  -- Status / moderation
  status            VARCHAR(20) DEFAULT 'active',  -- active | deleted | flagged | processing
  is_flagged        BOOLEAN DEFAULT false,
  flag_reason       TEXT,
  flagged_by        UUID REFERENCES users(id),
  flagged_at        TIMESTAMPTZ,

  created_at        TIMESTAMPTZ DEFAULT NOW(),
  deleted_at        TIMESTAMPTZ    -- soft delete
);

-- Indexes
CREATE INDEX idx_media_assets_uploader ON media_assets(uploader_id);
CREATE INDEX idx_media_assets_context  ON media_assets(context, context_id);
CREATE INDEX idx_media_assets_type     ON media_assets(asset_type);
CREATE INDEX idx_media_assets_status   ON media_assets(status);
CREATE INDEX idx_media_assets_created  ON media_assets(created_at DESC);

-- ═══ ALTER EXISTING TABLES — Add asset_id columns alongside existing URL columns ═══
-- (Keep old URL columns for backward compat — migrate gradually)

-- Users
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_asset_id UUID REFERENCES media_assets(id);

-- Parlors
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS logo_asset_id   UUID REFERENCES media_assets(id);
ALTER TABLE parlors ADD COLUMN IF NOT EXISTS cover_asset_id  UUID REFERENCES media_assets(id);

-- Post media (existing post_media table if exists, or add to posts)
ALTER TABLE post_media ADD COLUMN IF NOT EXISTS asset_id UUID REFERENCES media_assets(id);

-- Stories
ALTER TABLE stories ADD COLUMN IF NOT EXISTS asset_id UUID REFERENCES media_assets(id);

-- Messages
ALTER TABLE messages ADD COLUMN IF NOT EXISTS asset_id UUID REFERENCES media_assets(id);

-- Ratings (review photos)
ALTER TABLE ratings ADD COLUMN IF NOT EXISTS review_asset_ids UUID[];

-- Tournaments
ALTER TABLE tournaments ADD COLUMN IF NOT EXISTS cover_asset_id UUID REFERENCES media_assets(id);

-- Events (parlour_events)
ALTER TABLE parlour_events ADD COLUMN IF NOT EXISTS cover_asset_id UUID REFERENCES media_assets(id);

-- Community posts
ALTER TABLE community_posts ADD COLUMN IF NOT EXISTS asset_ids UUID[];

-- Parlour gallery
ALTER TABLE parlour_gallery ADD COLUMN IF NOT EXISTS asset_id UUID REFERENCES media_assets(id);
```

---

## ALL DMS API ENDPOINTS

### Upload Flow (3 steps)
```
Step 1 — Request upload slot:
POST /dms/upload-intent
Headers: Authorization: Bearer {jwt}
Body: {
  file_type: "image/jpeg",          -- MIME type
  file_name: "photo.jpg",           -- Original filename
  file_size: 2048576,               -- Bytes
  asset_type: "image",              -- image | video | document | audio
  context: "post_media",            -- where it will be used
  context_id: "uuid-optional"       -- related entity id (can be null if not yet created)
}
Response: {
  asset_id: "uuid",
  upload_url: "https://s3.amazonaws.com/...",  -- Pre-signed PUT URL (expires 15min)
  cdn_url: "https://cdn.parlour.in/..."        -- Final public URL after upload
}

Step 2 — Upload directly to S3:
PUT {upload_url}  (client does this directly, no server involved)
Headers: Content-Type: {file_type}
Body: [raw file bytes]

Step 3 — Confirm upload:
POST /dms/confirm-upload
Body: {
  asset_id: "uuid",
  width_px: 1920,        -- optional, client can send if known
  height_px: 1080,
  duration_seconds: 45.2 -- for video/audio
}
Response: {
  asset_id: "uuid",
  cdn_url: "https://cdn.parlour.in/...",
  thumbnail_url: "https://cdn.parlour.in/...thumb.jpg",  -- null for non-video
  status: "active"
}
```

### Asset Operations
```
GET    /dms/assets/{id}              → full asset metadata + cdn_url
DELETE /dms/assets/{id}             → soft delete (own assets only)
GET    /dms/assets?context=post_media&context_id=&type=image&page=1&limit=20
                                    → list assets with filters

PATCH  /dms/assets/{id}/context     → update context_id after entity creation
       body: {context_id: "uuid"}
```

### Admin DMS
```
GET    /admin/dms                   → all assets, paginated
       ?type=image|video|document|audio
       &context=post_media|user_avatar|...
       &uploader_id=
       &is_flagged=true|false
       &status=active|deleted|flagged
       &date_from=&date_to=
       &page=&limit=
       → PaginatedResponse<MediaAssetAdminItem>

GET    /admin/dms/stats             → storage breakdown by type, context, total size
GET    /admin/dms/orphans           → assets with no context_id (unlinked)
DELETE /admin/dms/{id}             → hard delete from S3 + DB
PATCH  /admin/dms/{id}/flag        → body: {is_flagged: bool, reason?: str}
PATCH  /admin/dms/{id}/status      → body: {status: 'active'|'deleted'|'flagged'}
POST   /admin/dms/bulk-delete      → body: {asset_ids: []}
```

---

## BACKEND DMS SERVICE

```python
# backend/app/services/dms_service.py — COMPLETE IMPLEMENTATION

import uuid, math
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import boto3
from botocore.exceptions import ClientError
from ..models.media_asset import MediaAsset
from ..config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

ALLOWED_MIME_TYPES = {
    "image": ["image/jpeg", "image/png", "image/webp", "image/gif"],
    "video": ["video/mp4", "video/quicktime", "video/webm"],
    "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/m4a"],
    "document": ["application/pdf", "application/msword",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "text/plain"],
}
MAX_FILE_SIZES = {
    "image": 15 * 1024 * 1024,    # 15 MB
    "video": 500 * 1024 * 1024,   # 500 MB
    "audio": 50 * 1024 * 1024,    # 50 MB
    "document": 25 * 1024 * 1024, # 25 MB
}
UPLOAD_URL_EXPIRY = 900  # 15 minutes


def _format_size(bytes_: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def _s3_key(asset_type: str, asset_id: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"media/{asset_type}/{asset_id[:2]}/{asset_id}.{ext}"


async def create_upload_intent(
    uploader_id: str,
    file_type: str,
    file_name: str,
    file_size: int,
    asset_type: str,
    context: str,
    context_id: str | None,
    db: AsyncSession,
) -> dict:
    # Validate
    if asset_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"Unsupported asset_type: {asset_type}")
    if file_type not in ALLOWED_MIME_TYPES[asset_type]:
        raise HTTPException(400, f"File type {file_type} not allowed for {asset_type}")
    if file_size > MAX_FILE_SIZES[asset_type]:
        max_mb = MAX_FILE_SIZES[asset_type] // (1024 * 1024)
        raise HTTPException(413, f"File too large. Max {max_mb}MB for {asset_type}")

    asset_id = str(uuid.uuid4())
    s3_key = _s3_key(asset_type, asset_id, file_name)
    cdn_url = f"{settings.AWS_CLOUDFRONT_URL}/{s3_key}"

    # Pre-signed URL for direct S3 upload
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.AWS_S3_BUCKET,
            "Key": s3_key,
            "ContentType": file_type,
            "ContentLength": file_size,
        },
        ExpiresIn=UPLOAD_URL_EXPIRY,
    )

    # Create DB record with status='processing'
    asset = MediaAsset(
        id=asset_id,
        uploader_id=uploader_id,
        original_filename=file_name,
        file_type=file_type,
        asset_type=asset_type,
        file_size_bytes=file_size,
        file_size_label=_format_size(file_size),
        s3_key=s3_key,
        s3_bucket=settings.AWS_S3_BUCKET,
        cdn_url=cdn_url,
        context=context,
        context_id=context_id,
        status="processing",
    )
    db.add(asset)
    await db.commit()

    return {
        "asset_id": asset_id,
        "upload_url": presigned_url,
        "cdn_url": cdn_url,
    }


async def confirm_upload(
    asset_id: str,
    uploader_id: str,
    width_px: int | None,
    height_px: int | None,
    duration_seconds: float | None,
    db: AsyncSession,
) -> dict:
    asset = (await db.execute(
        select(MediaAsset).where(
            MediaAsset.id == asset_id,
            MediaAsset.uploader_id == uploader_id,
            MediaAsset.status == "processing",
        )
    )).scalar_one_or_none()

    if not asset:
        raise HTTPException(404, "Asset not found or already confirmed")

    # Verify file actually exists in S3
    try:
        s3_client.head_object(Bucket=asset.s3_bucket, Key=asset.s3_key)
    except ClientError:
        raise HTTPException(422, "File not found in S3. Upload may have failed.")

    asset.width_px = width_px
    asset.height_px = height_px
    asset.duration_seconds = duration_seconds
    asset.status = "active"

    # Queue thumbnail generation for video (Celery task)
    if asset.asset_type == "video":
        from ..tasks.media_tasks import generate_video_thumbnail
        generate_video_thumbnail.delay(asset_id, asset.cdn_url)

    await db.commit()
    await db.refresh(asset)

    return {
        "asset_id": asset.id,
        "cdn_url": asset.cdn_url,
        "thumbnail_url": asset.thumbnail_url,
        "status": "active",
    }


async def get_asset(asset_id: str, db: AsyncSession) -> MediaAsset:
    asset = (await db.execute(
        select(MediaAsset).where(
            MediaAsset.id == asset_id,
            MediaAsset.status != "deleted",
        )
    )).scalar_one_or_none()
    if not asset:
        raise HTTPException(404, "Asset not found")
    return asset


async def soft_delete_asset(asset_id: str, requester_id: str, db: AsyncSession):
    asset = (await db.execute(
        select(MediaAsset).where(MediaAsset.id == asset_id)
    )).scalar_one_or_none()
    if not asset:
        raise HTTPException(404, "Asset not found")
    if str(asset.uploader_id) != requester_id:
        raise HTTPException(403, "Not your asset")
    asset.status = "deleted"
    asset.deleted_at = datetime.now(timezone.utc)
    await db.commit()
```

---

## FLUTTER DMS SERVICE + WIDGET

### DMS Service (lib/core/services/dms_service.dart)
```dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

final dmsServiceProvider = Provider<DmsService>((ref) => DmsService(ref.read(dioClientProvider)));

class DmsUploadResult {
  final String assetId;
  final String cdnUrl;
  final String? thumbnailUrl;
  DmsUploadResult({required this.assetId, required this.cdnUrl, this.thumbnailUrl});
}

class DmsService {
  final Dio _dio;
  DmsService(this._dio);

  /// Full upload flow: intent → S3 upload → confirm → return result
  Future<DmsUploadResult> uploadFile({
    required File file,
    required String assetType,     // image | video | document | audio
    required String fileType,      // MIME type
    required String context,       // post_media | user_avatar | story | message | etc.
    String? contextId,
    void Function(double progress)? onProgress,  // 0.0 to 1.0
  }) async {
    final fileSize = await file.length();
    final fileName = file.path.split('/').last;

    // Step 1: Request upload intent
    final intentRes = await _dio.post('/dms/upload-intent', data: {
      'file_type': fileType,
      'file_name': fileName,
      'file_size': fileSize,
      'asset_type': assetType,
      'context': context,
      if (contextId != null) 'context_id': contextId,
    });
    final assetId   = intentRes.data['asset_id'] as String;
    final uploadUrl = intentRes.data['upload_url'] as String;
    final cdnUrl    = intentRes.data['cdn_url'] as String;

    // Step 2: Upload directly to S3 with progress
    final fileBytes = await file.readAsBytes();
    final req = http.Request('PUT', Uri.parse(uploadUrl))
      ..headers['Content-Type'] = fileType
      ..bodyBytes = fileBytes;

    int bytesSent = 0;
    final streamedRes = await req.send();
    await for (final chunk in streamedRes.stream) {
      bytesSent += chunk.length;
      onProgress?.call(bytesSent / fileSize);
    }
    if (streamedRes.statusCode != 200) {
      throw Exception('S3 upload failed: ${streamedRes.statusCode}');
    }

    // Step 3: Confirm upload
    final confirmRes = await _dio.post('/dms/confirm-upload', data: {
      'asset_id': assetId,
    });

    return DmsUploadResult(
      assetId: assetId,
      cdnUrl: cdnUrl,
      thumbnailUrl: confirmRes.data['thumbnail_url'],
    );
  }

  Future<Map<String, dynamic>> getAsset(String assetId) async {
    final r = await _dio.get('/dms/assets/$assetId');
    return r.data;
  }

  Future<void> deleteAsset(String assetId) async {
    await _dio.delete('/dms/assets/$assetId');
  }

  Future<void> updateContext(String assetId, String contextId) async {
    await _dio.patch('/dms/assets/$assetId/context', data: {'context_id': contextId});
  }
}
```

### DMS Upload Widget (lib/shared/widgets/dms_upload_widget.dart)
```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/services/dms_service.dart';

/// Universal reusable upload widget.
/// Shows upload progress, preview, and returns (assetId, cdnUrl).
class DmsUploadWidget extends ConsumerStatefulWidget {
  final String context;           // 'post_media' | 'user_avatar' | 'story' | etc.
  final String? contextId;
  final List<String> allowedTypes; // ['image'] | ['image','video'] | ['document']
  final String? existingCdnUrl;   // Show existing asset if editing
  final void Function(DmsUploadResult result) onUploaded;
  final void Function()? onRemoved;
  final double? height;
  final bool showPreview;
  final Widget? placeholder;

  const DmsUploadWidget({
    required this.context,
    required this.allowedTypes,
    required this.onUploaded,
    this.contextId,
    this.existingCdnUrl,
    this.onRemoved,
    this.height = 180,
    this.showPreview = true,
    this.placeholder,
    super.key,
  });

  @override
  ConsumerState<DmsUploadWidget> createState() => _DmsUploadWidgetState();
}

class _DmsUploadWidgetState extends ConsumerState<DmsUploadWidget> {
  double? _progress;
  bool _uploading = false;
  String? _previewPath;
  String? _cdnUrl;
  String? _error;

  Future<void> _pickAndUpload() async {
    File? file;
    String? mimeType;

    if (widget.allowedTypes.contains('image') && widget.allowedTypes.length == 1) {
      final picked = await ImagePicker().pickImage(source: ImageSource.gallery, imageQuality: 85);
      if (picked == null) return;
      file = File(picked.path);
      mimeType = 'image/jpeg';
    } else if (widget.allowedTypes.contains('video')) {
      final picked = await ImagePicker().pickVideo(source: ImageSource.gallery);
      if (picked == null) return;
      file = File(picked.path);
      mimeType = 'video/mp4';
    } else {
      // Documents
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx', 'txt'],
      );
      if (result == null || result.files.isEmpty) return;
      file = File(result.files.first.path!);
      mimeType = 'application/pdf';
    }

    setState(() { _uploading = true; _error = null; _previewPath = file!.path; _progress = 0; });

    try {
      final dms = ref.read(dmsServiceProvider);
      final result = await dms.uploadFile(
        file: file,
        assetType: widget.allowedTypes.first,
        fileType: mimeType,
        context: widget.context,
        contextId: widget.contextId,
        onProgress: (p) => setState(() => _progress = p),
      );
      setState(() { _cdnUrl = result.cdnUrl; _uploading = false; _progress = null; });
      widget.onUploaded(result);
    } catch (e) {
      setState(() { _error = 'Upload failed. Tap to retry.'; _uploading = false; _progress = null; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayUrl = _cdnUrl ?? widget.existingCdnUrl;

    return GestureDetector(
      onTap: _uploading ? null : _pickAndUpload,
      child: Container(
        height: widget.height,
        decoration: BoxDecoration(
          color: const Color(0xFFF5F5F5),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _error != null ? Colors.red : const Color(0xFFE0E0E0),
            style: BorderStyle.solid,
          ),
        ),
        child: _uploading
            ? _UploadingState(progress: _progress ?? 0)
            : displayUrl != null && widget.showPreview
                ? _PreviewState(cdnUrl: displayUrl, localPath: _previewPath,
                    onRemove: widget.onRemoved == null ? null : () {
                      setState(() { _cdnUrl = null; });
                      widget.onRemoved?.call();
                    })
                : _EmptyState(
                    allowedTypes: widget.allowedTypes,
                    error: _error,
                    placeholder: widget.placeholder,
                  ),
      ),
    );
  }
}

class _UploadingState extends StatelessWidget {
  final double progress;
  const _UploadingState({required this.progress});
  @override
  Widget build(BuildContext context) {
    return Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      CircularProgressIndicator(value: progress, color: const Color(0xFF7367F0), strokeWidth: 3),
      const SizedBox(height: 12),
      Text('${(progress * 100).toInt()}%', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF7367F0))),
      const SizedBox(height: 4),
      const Text('Uploading...', style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
    ]);
  }
}

class _PreviewState extends StatelessWidget {
  final String cdnUrl;
  final String? localPath;
  final VoidCallback? onRemove;
  const _PreviewState({required this.cdnUrl, this.localPath, this.onRemove});
  @override
  Widget build(BuildContext context) {
    return Stack(fit: StackFit.expand, children: [
      ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: localPath != null
            ? Image.file(File(localPath!), fit: BoxFit.cover)
            : CachedNetworkImage(imageUrl: cdnUrl, fit: BoxFit.cover),
      ),
      if (onRemove != null)
        Positioned(top: 8, right: 8,
          child: GestureDetector(
            onTap: onRemove,
            child: Container(
              width: 28, height: 28,
              decoration: const BoxDecoration(color: Colors.black54, shape: BoxShape.circle),
              child: const Icon(Icons.close, color: Colors.white, size: 16),
            ),
          ),
        ),
    ]);
  }
}

class _EmptyState extends StatelessWidget {
  final List<String> allowedTypes;
  final String? error;
  final Widget? placeholder;
  const _EmptyState({required this.allowedTypes, this.error, this.placeholder});
  @override
  Widget build(BuildContext context) {
    if (error != null) {
      return Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.error_outline, color: Colors.red, size: 32),
        const SizedBox(height: 8),
        Text(error!, style: const TextStyle(color: Colors.red, fontSize: 13), textAlign: TextAlign.center),
      ]);
    }
    if (placeholder != null) return Center(child: placeholder!);
    final icon = allowedTypes.first == 'image' ? Icons.image_outlined
        : allowedTypes.first == 'video' ? Icons.videocam_outlined
        : allowedTypes.first == 'document' ? Icons.description_outlined
        : Icons.upload_file_outlined;
    return Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Icon(icon, color: const Color(0xFFBBBBBB), size: 36),
      const SizedBox(height: 8),
      Text('Tap to upload ${allowedTypes.join(' or ')}',
          style: const TextStyle(fontSize: 13, color: Color(0xFF999999))),
    ]);
  }
}
```

---

## WHERE DmsUploadWidget IS USED (replace all existing upload flows)

```dart
// ── 1. User Avatar (ProfileEditScreen)
DmsUploadWidget(
  context: 'user_avatar',
  allowedTypes: ['image'],
  height: 100,
  existingCdnUrl: user.avatarUrl,
  onUploaded: (result) {
    ref.read(profileProvider.notifier).updateAvatar(result.assetId, result.cdnUrl);
  },
)

// ── 2. Post Media (CreatePostScreen) — Multiple files
// Use DmsMultiUploadWidget (list of DmsUploadWidget instances)
// Returns: List<DmsUploadResult>

// ── 3. Story (StoryCreatorScreen)
DmsUploadWidget(
  context: 'story',
  allowedTypes: ['image', 'video'],
  onUploaded: (result) => storyAssetId = result.assetId,
)

// ── 4. Chat Message (ChatScreen)
DmsUploadWidget(
  context: 'message',
  allowedTypes: ['image', 'video', 'document'],
  showPreview: false,
  onUploaded: (result) {
    ref.read(messagesProvider(convId).notifier).sendMediaMessage(result.assetId);
  },
)

// ── 5. Parlor Logo (ParlourSettingsScreen)
DmsUploadWidget(context: 'parlor_logo', allowedTypes: ['image'], ...)

// ── 6. Review Photo (RatingScreen)
DmsUploadWidget(context: 'review_photo', allowedTypes: ['image'], ...)

// ── 7. Tournament Cover (CreateTournamentScreen)
DmsUploadWidget(context: 'tournament_cover', allowedTypes: ['image'], ...)
```

---

## EXISTING CODE CHANGES — What to Replace

```
FIND → REPLACE

1. In all upload flows:
   OLD: POST /uploads/presigned-url {file_type, purpose}
   NEW: POST /dms/upload-intent {file_type, file_name, file_size, asset_type, context}

2. In all DB inserts:
   OLD: post.media_urls = [cdn_url_1, cdn_url_2]
   NEW: post_media.asset_id = asset_id_1, asset_id_2

3. In all image/video display:
   OLD: CachedNetworkImage(imageUrl: post.mediaUrls[0])
   NEW: CachedNetworkImage(imageUrl: post.postMedia[0].asset.cdnUrl)
        OR: CachedNetworkImage(imageUrl: cdnUrlFromAssetId(assetId))
   NOTE: cdn_url is always stored in media_assets table, so once joined it's one DB query

4. In admin:
   OLD: Nothing specific for media
   NEW: /admin/dms section with media library browser
```

---

## ADMIN ANGULAR DMS SECTION

### New Page: AdminDmsPage (src/pages/dms/DmsPage)
```
URL: /admin/dms

LAYOUT:
  Left sidebar (280px): FILTER PANEL
    Asset Type: [All] [🖼 Images] [🎥 Videos] [📄 Documents] [🔊 Audio]
    Context:    Dropdown — all contexts
    Status:     [Active] [Flagged] [Deleted]
    Date range: From → To
    Uploader:   Search input
    [Apply Filters] [Reset]

  Right main area:
    TOP BAR:
      Search input (search by filename)
      View toggle: [⊞ Grid] [☰ List]
      [Bulk Actions ↓] — Delete, Flag, Export
      Pagination info: "1,234 assets · 2.4 GB total"
    
    STATS CARDS ROW:
      Total Assets | Total Storage | Images | Videos | Documents | Flagged

    GRID VIEW (4 columns desktop, 2 mobile):
      Each card:
        [Thumbnail or file icon]
        Filename (truncated)
        Size badge (2.4 MB)
        Type badge (color-coded)
        Uploader + date
        Context chip (post_media, user_avatar, etc.)
        Actions: [👁 View] [🚩 Flag] [🗑 Delete]
    
    LIST VIEW:
      DataTable: Thumbnail | Filename | Type | Size | Context | Uploader | Date | Status | Actions
```

### Storage Stats (sub-page: /admin/dms/stats)
```
  Donut chart: storage by type (Images/Videos/Documents/Audio)
  Bar chart: uploads per day (30 days)
  Table: Top uploaders by storage used
  Table: Most uploaded contexts
  [Download Report CSV] button
```

### Orphaned Assets (/admin/dms/orphans)
```
  Assets where context_id IS NULL and created_at < 24 hours ago
  (uploaded but never linked to any entity)
  Table: filename, size, type, uploaded_by, uploaded_at, [Delete] button
  [Bulk Delete All Orphans] button
```

---

## NEW FLUTTER PACKAGES NEEDED
```yaml
dependencies:
  file_picker: ^8.0.7         # Pick documents (PDF, DOCX, etc.)
  # Already have: image_picker, cached_network_image
  # Already have: dio, flutter_riverpod
```

---

## BACKEND PACKAGES NEEDED
```bash
pip install pillow  # Image metadata extraction (already likely installed)
pip install python-magic  # Better MIME type detection (optional)
```

---

## CODING RULES
1. EVERY file upload in the app MUST go through DMS service. No direct S3 uploads.
2. Store asset_id in DB, never raw URLs (cdn_url is denormalized for performance — OK).
3. DmsUploadWidget is the ONLY upload UI component — all screens use it.
4. Asset confirmation MUST be called after S3 upload — no orphan assets.
5. Admin can hard-delete from S3 + DB. Users can only soft-delete.
6. Context tagging is REQUIRED at upload intent time.
7. All existing `presigned-url` endpoint calls → replace with `dms/upload-intent`.

---

## START: `cat PROGRESS_DMS.md` → build first unchecked task.
