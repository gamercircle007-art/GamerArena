"""Upload domain — S3 presigned URL generation."""

import uuid

from app.core.config import Settings
from app.domains.common.exceptions import ValidationError


class UploadService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_presigned_url(self, file_type: str, purpose: str) -> dict[str, str]:
        allowed_prefixes = ("image/", "video/", "audio/")
        if not file_type.startswith(allowed_prefixes):
            raise ValidationError("Only image, video, and audio uploads are supported")

        ext = file_type.split("/")[-1]
        if ext == "quicktime":
            ext = "mov"
        key = f"{purpose}/{uuid.uuid4()}.{ext}"

        if not self.settings.aws_s3_bucket:
            base = "https://dev-cdn.example.com"
            return {
                "upload_url": f"{base}/upload-stub/{key}",
                "public_url": f"{base}/{key}",
                "key": key,
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
        return {"upload_url": upload_url, "public_url": public_url, "key": key}