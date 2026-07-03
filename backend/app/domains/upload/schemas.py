"""Upload domain Pydantic schemas."""

from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    file_type: str = Field(..., examples=["image/jpeg"])
    purpose: str = Field(..., examples=["post_media"])


class PresignedUrlResponse(BaseModel):
    upload_url: str
    public_url: str
    key: str
    asset_id: str | None = None
    cdn_url: str | None = None