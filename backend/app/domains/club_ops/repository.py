"""Club scoping + data access for club operations.

**This module is the multi-tenant boundary.** Every club-ops endpoint resolves its
`parlor_id` through `ClubScope` before touching any table. Scoping is enforced here at
the query layer — not in the router, and never only in the UI.

Ownership model (confirmed in discovery, not assumed): a club is a `gaming_places` row,
and ownership lives on `gaming_place_extensions.owner_id`. There is no staff/membership
table, so "the owner's clubs" is the set of extensions with `owner_id == user.id`.
Today that set holds at most one club (`ParlorService.create_parlor` rejects a second),
but everything here is written set-based so adding co-owners later does not need a
rewrite of the callers.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import ForbiddenError, NotFoundError
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension
from app.domains.user.models import UserRole

_ADMIN_ROLES = (UserRole.ADMIN.value, "admin")


def _role_of(user) -> str:
    role = getattr(user, "role", None)
    return role.value if hasattr(role, "value") else str(role)


def is_platform_admin(user) -> bool:
    return _role_of(user) in _ADMIN_ROLES


class ClubScope:
    """Resolves and enforces which club(s) a caller may act on."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def owned_club_ids(self, user) -> list[UUID]:
        """Club ids this user owns. Empty list for a plain user."""
        rows = (
            await self.session.execute(
                select(GamingPlaceExtension.gaming_place_id).where(
                    GamingPlaceExtension.owner_id == user.id,
                    GamingPlaceExtension.is_deleted.is_(False),
                )
            )
        ).scalars().all()
        return list(rows)

    async def resolve_club_id(self, user, parlor_id: UUID | None = None) -> UUID:
        """Return the club id this request operates on, or raise.

        - Platform admin: may name any existing club, but must name one explicitly.
        - Owner: may name one of their own clubs; if they omit it and own exactly one,
          it is inferred (the common case, since ownership is 1:1 today).

        Raises ForbiddenError (-> 403) on a cross-club attempt, NotFoundError (-> 404)
        when the club id does not exist at all.
        """
        if is_platform_admin(user):
            if parlor_id is None:
                raise ForbiddenError("parlor_id is required for admin access")
            await self._assert_exists(parlor_id)
            return parlor_id

        owned = await self.owned_club_ids(user)
        if not owned:
            raise ForbiddenError("You do not manage a club")

        if parlor_id is None:
            if len(owned) == 1:
                return owned[0]
            raise ForbiddenError("parlor_id is required when you manage multiple clubs")

        if parlor_id not in owned:
            # Deliberately 403 and not 404: the caller is authenticated and the club may
            # well exist — it just isn't theirs. Phase 5 asserts this exact status.
            raise ForbiddenError("This club is not yours")
        return parlor_id

    async def _assert_exists(self, parlor_id: UUID) -> None:
        found = (
            await self.session.execute(select(GamingPlace.id).where(GamingPlace.id == parlor_id))
        ).scalar_one_or_none()
        if found is None:
            raise NotFoundError("Club not found")


def scoped(stmt: Select, column, parlor_id: UUID) -> Select:
    """Apply the club filter to a select. Use this rather than hand-writing the where
    clause, so every club-ops query is greppable and provably scoped."""
    return stmt.where(column == parlor_id)
