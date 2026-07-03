"""Celery tasks for DMS media processing."""

from app.tasks.celery_app import celery_app


@celery_app.task(name="generate_video_thumbnail")
def generate_video_thumbnail(asset_id: str, video_cdn_url: str) -> None:
    """
    Generate a video thumbnail and store in S3.

    Requires ffmpeg on the worker host. Stub-safe when ffmpeg is unavailable.
    """
    try:
        import subprocess
        import tempfile
        import uuid
        from pathlib import Path

        from app.core.config import get_settings

        settings = get_settings()
        if not settings.aws_s3_bucket:
            return

        with tempfile.TemporaryDirectory() as tmp:
            thumb_path = Path(tmp) / f"{asset_id}_thumb.jpg"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    "1",
                    "-i",
                    video_cdn_url,
                    "-vframes",
                    "1",
                    "-q:v",
                    "2",
                    str(thumb_path),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )

            import boto3
            from sqlalchemy import create_engine, text

            thumb_key = f"media/thumbnails/{asset_id}_thumb.jpg"
            cdn_thumb = f"https://{settings.aws_cloudfront_domain}/{thumb_key}"

            client = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id or None,
                aws_secret_access_key=settings.aws_secret_access_key or None,
            )
            client.upload_file(
                str(thumb_path),
                settings.aws_s3_bucket,
                thumb_key,
                ExtraArgs={"ContentType": "image/jpeg"},
            )

            sync_url = settings.database_url.replace("+asyncpg", "").replace(
                "postgresql+psycopg", "postgresql"
            )
            engine = create_engine(sync_url)
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "UPDATE media_assets SET thumbnail_url = :thumb WHERE id = :id"
                    ),
                    {"thumb": cdn_thumb, "id": uuid.UUID(asset_id)},
                )
    except Exception:
        return