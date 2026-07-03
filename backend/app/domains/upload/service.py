"""Upload domain — legacy presigned URLs, now delegates to DMS."""

import uuid

from app.core.config import Settings
from app.domains.common.exceptions import ValidationError
from app.domains.dms.service import ALLOWED_MIME_TYPES


class UploadService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_presigned_url(self, file_type: str, purpose: str) -> dict[str, str]:
        """Legacy endpoint — maps purpose to DMS context and returns compatible shape."""
        allowed_prefixes = tuple(
            mime for types in ALLOWED_MIME_TYPES.values() for mime in types
        )
        if not any(file_type.startswith(p.split("/")[0] + "/") for p in allowed_prefixes):
            if not file_type.startswith(("image/", "video/", "audio/", "application/")):
                raise ValidationError("Only image, video, audio, and document uploads are supported")

        asset_type = "image"
        if file_type.startswith("video/"):
            asset_type = "video"
        elif file_type.startswith("audio/"):
            asset_type = "audio"
        elif file_type.startswith("application/") or file_type == "text/plain":
            asset_type = "document"

        ext = file_type.split("/")[-1]
        if ext == "quicktime":
            ext = "mov"
        asset_id = str(uuid.uuid4())
        key = f"media/{asset_type}/{asset_id[:2]}/{asset_id}.{ext}"

        if not self.settings.aws_s3_bucket:
            base = "https://dev-cdn.example.com"
            return {
                "upload_url": f"{base}/upload-stub/{key}",
                "public_url": f"{base}/{key}",
                "key": key,
                "asset_id": asset_id,
                "cdn_url": f"{base}/{key}",
            }

        import boto3

        client = boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
        )
        upload_url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.settings.aws_s3_bucket,
                "Key": key,
                "ContentType": file_type,
            },
            ExpiresIn=3600,
        )
        public_url = f"https://{self.settings.aws_cloudfront_domain}/{key}"
        return {
            "upload_url": upload_url,
            "public_url": public_url,
            "key": key,
            "asset_id": asset_id,
            "cdn_url": public_url,
        }