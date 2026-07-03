"""Upload domain API routes."""

from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, SettingsDep
from app.domains.upload.schemas import PresignedUrlRequest, PresignedUrlResponse
from app.domains.upload.service import UploadService

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def create_presigned_url(
    body: PresignedUrlRequest,
    settings: SettingsDep,
    current_user: CurrentUserDep,
) -> PresignedUrlResponse:
    _ = current_user
    result = UploadService(settings).create_presigned_url(body.file_type, body.purpose)
    return PresignedUrlResponse(**result)