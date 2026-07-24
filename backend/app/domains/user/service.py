"""User domain business logic."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import UserLocationUpdate, UserResponse, UserUpdate


class UserService:
    """User domain service — orchestrates repository operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def get_user(self, user_id: UUID) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)

    async def get_or_create_by_identifier(
        self,
        email: str | None = None,
        phone: str | None = None,
    ) -> UserResponse:
        if not email and not phone:
            raise ValidationError("Either email or phone is required")

        user = await self.repo.get_by_email_or_phone(email, phone)
        if user is None:
            user = await self.repo.create(email=email, phone=phone)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        if data.name is not None:
            user.full_name = data.name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        if data.bio is not None:
            user.bio = data.bio
        if data.city is not None:
            user.city = data.city
        await self.repo.session.flush()
        await self.repo.session.refresh(user)
        return UserResponse.model_validate(user)

    async def update_location(
        self,
        user_id: UUID,
        data: UserLocationUpdate,
    ) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.latitude = data.latitude
        user.longitude = data.longitude
        user.city = data.city
        user.country = data.country.upper() if data.country else None
        user.location_updated_at = datetime.now(UTC)
        await self.repo.session.flush()
        await self.repo.session.refresh(user)
        return UserResponse.model_validate(user)