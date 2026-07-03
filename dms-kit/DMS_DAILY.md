# GROK — DMS DAILY SESSION
# Paste at the start of EVERY Grok session for DMS work.
# ─────────────────────────────────────────────────────────────────────────────

You are building a centralized DMS (Document Management System) for the GameConnect app.
ALL media (images, videos, documents) goes through DMS. Other modules store asset_id only.
Backend: Python FastAPI. Frontend: Flutter. Admin: Angular.

## Context Files
- `DMS_MASTER_CONTEXT.md` — full spec: DB schema, DMS service code, Flutter widget code, Admin UI
- `PROGRESS_DMS.md` — task checklist

## Do This Now
```bash
cat PROGRESS_DMS.md | grep "^\- \[ \]" | head -5
```
Find first unchecked `[ ]` → read relevant existing files → build it completely.

## Core Rules
- Every upload goes through: POST /dms/upload-intent → PUT S3 → POST /dms/confirm-upload
- Never store raw URLs in other tables — store asset_id (cdn_url cached in media_assets is OK)
- DmsUploadWidget is the ONLY upload UI — all screens use it
- Context tagging is REQUIRED: every asset must have context + context_id
- Backward compat: keep old URL columns, add new asset_id columns alongside

## Key Validations
- image: max 15MB, MIME: image/jpeg|png|webp|gif
- video: max 500MB, MIME: video/mp4|quicktime|webm
- document: max 25MB, MIME: application/pdf + word formats
- audio: max 50MB, MIME: audio/mpeg|wav|ogg|m4a

## Install (if not done)
```bash
flutter pub add file_picker           # Flutter — document picker
pip install ffmpeg-python pillow      # Backend — video thumbnails
```

## Run
```bash
uvicorn backend.app.main:app --reload --port 8000   # backend
flutter run                                          # flutter
```

## If Grok Loses Context
```
Re-read DMS_MASTER_CONTEXT.md. We were building task [TASK-ID]. Continue.
```

Start → `cat PROGRESS_DMS.md` → build next `[ ]`.
