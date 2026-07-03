"""User domain data access layer."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user.models import User


class UserRepository:
    """Repository pattern for User persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        normalized = self.normalize_phone(phone)
        result = await self.session.execute(select(User).where(User.phone == normalized))
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    async def phone_exists(self, phone: str) -> bool:
        return await self.get_by_phone(phone) is not None

    async def get_by_username(self, username: str) -> User | None:
        normalized = self.normalize_username(username)
        result = await self.session.execute(
            select(User).where(User.username == normalized)
        )
        return result.scalar_one_or_none()

    async def username_exists(self, username: str) -> bool:
        return await self.get_by_username(username) is not None

    async def get_by_email_or_phone(self, email: str | None, phone: str | None) -> User | None:
        conditions = []
        if email:
            conditions.append(User.email == email.lower())
        if phone:
            conditions.append(User.phone == self.normalize_phone(phone))
        if not conditions:
            return None
        result = await self.session.execute(select(User).where(or_(*conditions)))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str | None = None,
        phone: str | None = None,
        full_name: str | None = None,
    ) -> User:
        user = User(
            email=email.lower() if email else None,
            phone=self.normalize_phone(phone) if phone else None,
            full_name=full_name,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def create_with_password(
        self,
        *,
        full_name: str,
        username: str,
        email: str,
        phone: str,
        hashed_password: str,
    ) -> User:
        user = User(
            full_name=full_name.strip(),
            username=self.normalize_username(username),
            email=email.lower().strip(),
            phone=self.normalize_phone(phone),
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            email_verified=True,
            phone_verified=True,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    @staticmethod
    def normalize_username(username: str) -> str:
        """Lowercase handle for case-insensitive uniqueness."""
        return username.strip().lower()

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize to E.164. Matches Flutter client (+91 for 10-digit IN numbers)."""
        cleaned = phone.strip()
        if cleaned.startswith("+"):
            digits = "".join(c for c in cleaned[1:] if c.isdigit())
            return f"+{digits}" if digits else cleaned

        digits = "".join(c for c in cleaned if c.isdigit())
        if len(digits) == 10:
            return f"+91{digits}"
        return f"+{digits.lstrip('0')}"