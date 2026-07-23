"""Admin domain business logic — parlors, moderation, analytics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.schemas import (
    AdminAssignOwner,
    AdminParlorCreate,
    AdminParlorUpdate,
    AdminUserPatch,
)
from app.domains.comment.models import Comment
from app.domains.gaming_booking.models import GamingBooking, GamingSlot, ParlourOffer, ParlourRating
from app.domains.gaming_place.mappers import resolve_media_url, to_view
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension
from app.domains.like.models import Like
from app.domains.notification.models import Notification
from app.domains.post.models import Post
from app.domains.reel.models import Reel
from app.domains.story.models import Story
from app.domains.tournament.models import Booking, Tournament
from app.domains.user.models import User, UserRole
from app.domains.user.schemas import UserResponse

# Synthetic city for admin-created venues when none supplied
_DEFAULT_CITY_ID = UUID("00000000-0000-4000-8000-000000000001")


def paginated(items: list, total: int, page: int, limit: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": page * limit < total,
    }


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Stats / Analytics ──────────────────────────────────────────────

    async def stats(self) -> dict:
        users = await self.session.scalar(select(func.count()).select_from(User)) or 0
        parlors = await self.session.scalar(select(func.count()).select_from(GamingPlace)) or 0
        tournaments = await self.session.scalar(select(func.count()).select_from(Tournament)) or 0
        posts = await self.session.scalar(select(func.count()).select_from(Post)) or 0
        gaming_bookings = (
            await self.session.scalar(select(func.count()).select_from(GamingBooking)) or 0
        )
        tournament_bookings = (
            await self.session.scalar(select(func.count()).select_from(Booking)) or 0
        )
        pending = (
            await self.session.scalar(
                select(func.count())
                .select_from(GamingPlaceExtension)
                .where(
                    GamingPlaceExtension.is_verified.is_(False),
                    GamingPlaceExtension.is_deleted.is_(False),
                )
            )
            or 0
        )
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        new_users_today = (
            await self.session.scalar(
                select(func.count()).select_from(User).where(User.created_at >= today_start)
            )
            or 0
        )
        revenue = await self.session.scalar(
            select(func.coalesce(func.sum(GamingBooking.final_price), 0)).where(
                GamingBooking.payment_status.in_(["paid", "completed", "success"])
            )
        )
        return {
            "users": int(users),
            "parlors": int(parlors),
            "tournaments": int(tournaments),
            "bookings": int(gaming_bookings) + int(tournament_bookings),
            "posts": int(posts),
            "revenue": float(revenue or 0),
            "new_users_today": int(new_users_today),
            "pending_verification": int(pending),
        }

    async def analytics(self, period: str = "30d") -> dict:
        days = 7 if period == "7d" else 90 if period == "90d" else 30
        since = datetime.now(UTC) - timedelta(days=days)

        user_growth = await self._daily_counts(User.created_at, since, days)
        bookings_per_day = await self._daily_counts(GamingBooking.created_at, since, days)
        posts_per_day = await self._daily_counts(Post.created_at, since, days)

        revenue_rows = await self.session.execute(
            select(
                func.date(GamingBooking.created_at).label("d"),
                func.coalesce(func.sum(GamingBooking.final_price), 0),
            )
            .where(
                GamingBooking.created_at >= since,
                GamingBooking.payment_status.in_(["paid", "completed", "success"]),
            )
            .group_by(func.date(GamingBooking.created_at))
            .order_by(func.date(GamingBooking.created_at))
        )
        revenue_map = {str(r[0]): float(r[1] or 0) for r in revenue_rows.all()}
        revenue_per_day = []
        for i in range(days):
            d = (since + timedelta(days=i)).date().isoformat()
            revenue_per_day.append({"date": d, "count": revenue_map.get(d, 0.0)})

        game_rows = await self.session.execute(
            select(GamingPlace.primary_type, func.count())
            .where(GamingPlace.primary_type.isnot(None))
            .group_by(GamingPlace.primary_type)
            .order_by(func.count().desc())
            .limit(10)
        )
        game_distribution = [
            {"label": (r[0] or "other").replace("_", " ").title(), "value": int(r[1])}
            for r in game_rows.all()
        ]

        top_rows = await self.session.execute(
            select(
                GamingBooking.parlour_id,
                GamingPlace.name,
                func.count(GamingBooking.id),
            )
            .join(GamingPlace, GamingPlace.id == GamingBooking.parlour_id)
            .where(GamingBooking.created_at >= since)
            .group_by(GamingBooking.parlour_id, GamingPlace.name)
            .order_by(func.count(GamingBooking.id).desc())
            .limit(10)
        )
        top_parlors = [
            {
                "parlor_id": str(r[0]),
                "parlor_name": r[1],
                "bookings_count": int(r[2]),
            }
            for r in top_rows.all()
        ]

        rev_top = await self.session.execute(
            select(
                GamingBooking.parlour_id,
                GamingPlace.name,
                func.coalesce(func.sum(GamingBooking.final_price), 0),
            )
            .join(GamingPlace, GamingPlace.id == GamingBooking.parlour_id)
            .where(
                GamingBooking.created_at >= since,
                GamingBooking.payment_status.in_(["paid", "completed", "success"]),
            )
            .group_by(GamingBooking.parlour_id, GamingPlace.name)
            .order_by(func.coalesce(func.sum(GamingBooking.final_price), 0).desc())
            .limit(10)
        )
        top_parlors_by_revenue = [
            {
                "parlor_id": str(r[0]),
                "parlor_name": r[1],
                "revenue": float(r[2] or 0),
            }
            for r in rev_top.all()
        ]

        total_users = await self.session.scalar(select(func.count()).select_from(User)) or 0
        new_users = (
            await self.session.scalar(
                select(func.count()).select_from(User).where(User.created_at >= since)
            )
            or 0
        )
        total_bookings = (
            await self.session.scalar(
                select(func.count())
                .select_from(GamingBooking)
                .where(GamingBooking.created_at >= since)
            )
            or 0
        )
        revenue = await self.session.scalar(
            select(func.coalesce(func.sum(GamingBooking.final_price), 0)).where(
                GamingBooking.created_at >= since,
                GamingBooking.payment_status.in_(["paid", "completed", "success"]),
            )
        )
        cancelled = (
            await self.session.scalar(
                select(func.count())
                .select_from(GamingBooking)
                .where(
                    GamingBooking.created_at >= since,
                    GamingBooking.booking_status.in_(["cancelled", "canceled"]),
                )
            )
            or 0
        )
        cancellation_rate = (
            round(float(cancelled) / float(total_bookings) * 100, 2) if total_bookings else 0.0
        )

        return {
            "period": period,
            "user_growth": user_growth,
            "bookings_per_day": bookings_per_day,
            "posts_per_day": posts_per_day,
            "revenue_per_day": revenue_per_day,
            "game_distribution": game_distribution,
            "top_parlors": top_parlors,
            "top_parlors_by_revenue": top_parlors_by_revenue,
            "total_users": int(total_users),
            "new_users": int(new_users),
            "total_bookings": int(total_bookings),
            "revenue": float(revenue or 0),
            "conversion_rate": 0.0,
            "cancellation_rate": cancellation_rate,
        }

    async def _daily_counts(self, col, since: datetime, days: int) -> list[dict]:
        rows = await self.session.execute(
            select(func.date(col).label("d"), func.count())
            .where(col >= since)
            .group_by(func.date(col))
            .order_by(func.date(col))
        )
        count_map = {str(r[0]): int(r[1]) for r in rows.all()}
        out = []
        for i in range(days):
            d = (since + timedelta(days=i)).date().isoformat()
            out.append({"date": d, "count": count_map.get(d, 0)})
        return out

    # ── Users ──────────────────────────────────────────────────────────

    async def soft_delete_user(self, user_id: UUID, actor_id: UUID) -> None:
        if str(user_id) == str(actor_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )
        user = await self._get_user(user_id)
        user.is_active = False
        await self.session.commit()

    async def update_user(self, user_id: UUID, body: AdminUserPatch) -> dict:
        user = await self._get_user(user_id)
        if body.is_active is not None:
            user.is_active = body.is_active
        if body.is_verified is not None:
            user.is_verified = body.is_verified
        if body.role is not None:
            try:
                user.role = UserRole(body.role)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role"
                ) from exc
        await self.session.commit()
        await self.session.refresh(user)
        return UserResponse.model_validate(user).model_dump(mode="json")

    async def _get_user(self, user_id: UUID) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    # ── Parlors (gaming_places + extensions) ───────────────────────────

    def _parlor_dict(self, place: GamingPlace, ext: GamingPlaceExtension | None) -> dict:
        view = to_view(place, ext)
        return {
            "id": str(view.id),
            "owner_id": str(view.owner_id) if view.owner_id else None,
            "name": view.name,
            "description": view.description,
            "logo_url": view.logo_url,
            "address": view.address,
            "latitude": view.latitude,
            "longitude": view.longitude,
            "game_types": view.game_types,
            "is_verified": view.is_verified,
            "follower_count": view.follower_count,
            "post_count": view.post_count,
            "is_following": False,
            "rating": view.rating,
            "phone": view.phone,
            "website": view.website,
            "is_active": view.is_active,
            "is_deleted": view.is_deleted,
            "business_status": place.business_status,
            "opening_hours": place.opening_hours,
            "price_per_hour": float(ext.price_per_hour) if ext and ext.price_per_hour is not None else None,
            "original_price": float(ext.original_price) if ext and ext.original_price is not None else None,
            "created_at": view.created_at.isoformat() if view.created_at else None,
            "updated_at": view.updated_at.isoformat() if view.updated_at else None,
        }

    async def list_parlors(
        self,
        *,
        page: int,
        limit: int,
        search: str | None,
        is_verified: bool | None,
        is_active: bool | None,
        include_deleted: bool = False,
    ) -> dict:
        page = max(1, page)
        limit = min(max(1, limit), 100)

        query = (
            select(GamingPlace, GamingPlaceExtension)
            .outerjoin(
                GamingPlaceExtension,
                GamingPlaceExtension.gaming_place_id == GamingPlace.id,
            )
        )
        if not include_deleted:
            query = query.where(
                or_(
                    GamingPlaceExtension.is_deleted.is_(False),
                    GamingPlaceExtension.gaming_place_id.is_(None),
                )
            )
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    GamingPlace.name.ilike(term),
                    GamingPlace.address.ilike(term),
                    GamingPlace.primary_type.ilike(term),
                    GamingPlace.phone.ilike(term),
                )
            )
        if is_verified is not None:
            if is_verified:
                query = query.where(GamingPlaceExtension.is_verified.is_(True))
            else:
                query = query.where(
                    or_(
                        GamingPlaceExtension.is_verified.is_(False),
                        GamingPlaceExtension.gaming_place_id.is_(None),
                    )
                )
        if is_active is not None:
            query = query.where(
                or_(
                    GamingPlaceExtension.is_active.is_(is_active),
                    GamingPlaceExtension.gaming_place_id.is_(None) if is_active else False,
                )
            )

        count_q = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_q) or 0
        result = await self.session.execute(
            query.order_by(GamingPlace.updated_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = [self._parlor_dict(place, ext) for place, ext in result.all()]
        return paginated(items, int(total), page, limit)

    async def get_parlor(self, parlor_id: UUID) -> dict:
        place, ext = await self._get_place_ext(parlor_id, allow_deleted=True)
        return self._parlor_dict(place, ext)

    async def create_parlor(self, body: AdminParlorCreate) -> dict:
        now = datetime.now(UTC)
        place_id = uuid4()
        types = body.game_types or ([body.primary_type] if body.primary_type else ["gaming"])
        place = GamingPlace(
            id=place_id,
            google_place_id=f"admin-{place_id}",
            name=body.name.strip(),
            address=body.address,
            city_id=body.city_id or _DEFAULT_CITY_ID,
            latitude=body.latitude,
            longitude=body.longitude,
            phone=body.phone,
            website=body.website,
            business_status="OPERATIONAL" if body.is_active else "CLOSED_TEMPORARILY",
            primary_type=body.primary_type or "gaming",
            types=types,
            opening_hours=body.opening_hours,
            image_url=body.image_url,
            created_at=now,
            updated_at=now,
        )
        self.session.add(place)

        if body.owner_id is not None:
            await self._ensure_owner_role(body.owner_id)

        ext = GamingPlaceExtension(
            gaming_place_id=place_id,
            owner_id=body.owner_id,
            is_verified=body.is_verified,
            is_active=body.is_active,
            is_deleted=False,
            price_per_hour=body.price_per_hour,
            original_price=body.original_price,
        )
        self.session.add(ext)
        await self.session.commit()
        await self.session.refresh(place)
        await self.session.refresh(ext)
        return self._parlor_dict(place, ext)

    async def update_parlor(self, parlor_id: UUID, body: AdminParlorUpdate) -> dict:
        place, ext = await self._get_place_ext(parlor_id, allow_deleted=True)
        if ext is None:
            ext = GamingPlaceExtension(gaming_place_id=place.id)
            self.session.add(ext)
            await self.session.flush()

        data = body.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            place.name = data["name"].strip()
        if "address" in data:
            place.address = data["address"]
        if "phone" in data:
            place.phone = data["phone"]
        if "website" in data:
            place.website = data["website"]
        if "image_url" in data:
            place.image_url = data["image_url"]
        if "latitude" in data:
            place.latitude = data["latitude"]
        if "longitude" in data:
            place.longitude = data["longitude"]
        if "primary_type" in data and data["primary_type"] is not None:
            place.primary_type = data["primary_type"]
        if "game_types" in data and data["game_types"] is not None:
            place.types = data["game_types"]
            if data["game_types"]:
                place.primary_type = data["game_types"][0]
        if "opening_hours" in data:
            place.opening_hours = data["opening_hours"]
        if "business_status" in data and data["business_status"] is not None:
            place.business_status = data["business_status"]
        if "is_verified" in data and data["is_verified"] is not None:
            ext.is_verified = data["is_verified"]
        if "is_active" in data and data["is_active"] is not None:
            ext.is_active = data["is_active"]
            if data["is_active"]:
                place.business_status = place.business_status or "OPERATIONAL"
            else:
                place.business_status = "CLOSED_TEMPORARILY"
        if "price_per_hour" in data:
            ext.price_per_hour = data["price_per_hour"]
        if "original_price" in data:
            ext.original_price = data["original_price"]
        if "owner_id" in data:
            if data["owner_id"] is not None:
                await self._ensure_owner_role(data["owner_id"])
            ext.owner_id = data["owner_id"]

        place.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(place)
        await self.session.refresh(ext)
        return self._parlor_dict(place, ext)

    async def verify_parlor(self, parlor_id: UUID, is_verified: bool) -> dict:
        place, ext = await self._get_place_ext(parlor_id)
        if ext is None:
            ext = GamingPlaceExtension(gaming_place_id=place.id, is_verified=is_verified)
            self.session.add(ext)
        else:
            ext.is_verified = is_verified
        place.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(place)
        await self.session.refresh(ext)
        return self._parlor_dict(place, ext)

    async def assign_owner(self, parlor_id: UUID, body: AdminAssignOwner) -> dict:
        place, ext = await self._get_place_ext(parlor_id)
        if ext is None:
            ext = GamingPlaceExtension(gaming_place_id=place.id)
            self.session.add(ext)
            await self.session.flush()
        if body.owner_id is not None:
            if body.promote_to_owner:
                await self._ensure_owner_role(body.owner_id)
            ext.owner_id = body.owner_id
        else:
            ext.owner_id = None
        place.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(place)
        await self.session.refresh(ext)
        return self._parlor_dict(place, ext)

    async def soft_delete_parlor(self, parlor_id: UUID) -> None:
        place, ext = await self._get_place_ext(parlor_id, allow_deleted=True)
        if ext is None:
            ext = GamingPlaceExtension(gaming_place_id=place.id)
            self.session.add(ext)
            await self.session.flush()
        ext.is_deleted = True
        ext.is_active = False
        ext.deleted_at = datetime.now(UTC)
        place.business_status = "CLOSED_PERMANENTLY"
        place.updated_at = datetime.now(UTC)
        await self.session.commit()

    async def restore_parlor(self, parlor_id: UUID) -> dict:
        place, ext = await self._get_place_ext(parlor_id, allow_deleted=True)
        if ext is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlor not found")
        ext.is_deleted = False
        ext.is_active = True
        ext.deleted_at = None
        place.business_status = "OPERATIONAL"
        place.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(place)
        await self.session.refresh(ext)
        return self._parlor_dict(place, ext)

    async def _get_place_ext(
        self, parlor_id: UUID, *, allow_deleted: bool = False
    ) -> tuple[GamingPlace, GamingPlaceExtension | None]:
        result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id == parlor_id)
        )
        place = result.scalar_one_or_none()
        if place is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlor not found")
        ext_result = await self.session.execute(
            select(GamingPlaceExtension).where(
                GamingPlaceExtension.gaming_place_id == parlor_id
            )
        )
        ext = ext_result.scalar_one_or_none()
        if ext is not None and ext.is_deleted and not allow_deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parlor not found")
        return place, ext

    async def _ensure_owner_role(self, user_id: UUID) -> None:
        user = await self._get_user(user_id)
        if user.role == UserRole.USER:
            user.role = UserRole.PARLOR_OWNER

    # ── Content moderation ─────────────────────────────────────────────

    async def list_posts(self, page: int, limit: int, search: str | None = None) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        query = select(Post)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(or_(Post.content.ilike(term), Post.title.ilike(term)))
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await self.session.execute(
            query.order_by(Post.created_at.desc()).offset((page - 1) * limit).limit(limit)
        )
        items = []
        for p in rows.scalars().all():
            items.append(
                {
                    "id": str(p.id),
                    "content": p.content,
                    "media_urls": p.media_urls or [],
                    "media_type": p.post_type or "post",
                    "parlor_id": str(p.parlor_id),
                    "tournament_id": str(p.tournament_id) if p.tournament_id else None,
                    "likes_count": p.likes_count,
                    "comments_count": p.comments_count,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def delete_post(self, post_id: UUID) -> None:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        await self.session.delete(post)
        await self.session.commit()

    async def list_reels(self, page: int, limit: int) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        total = (
            await self.session.scalar(
                select(func.count()).select_from(Reel).where(Reel.is_deleted.is_(False))
            )
            or 0
        )
        rows = await self.session.execute(
            select(Reel)
            .where(Reel.is_deleted.is_(False))
            .order_by(Reel.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = []
        for r in rows.scalars().all():
            items.append(
                {
                    "id": str(r.id),
                    "user_id": str(r.user_id),
                    "video_url": r.video_url,
                    "thumbnail_url": r.thumbnail_url,
                    "caption": r.caption,
                    "likes_count": r.likes_count,
                    "comments_count": r.comments_count,
                    "views_count": r.views_count,
                    "is_deleted": r.is_deleted,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def delete_reel(self, reel_id: UUID) -> None:
        result = await self.session.execute(select(Reel).where(Reel.id == reel_id))
        reel = result.scalar_one_or_none()
        if reel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reel not found")
        reel.is_deleted = True
        await self.session.commit()

    async def list_comments(self, page: int, limit: int, is_deleted: bool | None = None) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        query = select(Comment)
        if is_deleted is not None:
            query = query.where(Comment.is_deleted.is_(is_deleted))
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await self.session.execute(
            query.order_by(Comment.created_at.desc()).offset((page - 1) * limit).limit(limit)
        )
        items = []
        for c in rows.scalars().all():
            user = await self.session.get(User, c.user_id)
            items.append(
                {
                    "id": str(c.id),
                    "user_id": str(c.user_id),
                    "user": {
                        "id": str(user.id),
                        "name": user.full_name,
                        "avatar_url": user.avatar_url,
                    }
                    if user
                    else None,
                    "content": c.content if not c.is_deleted else "[removed]",
                    "parent_id": str(c.parent_id) if c.parent_id else None,
                    "likes_count": c.likes_count,
                    "is_deleted": c.is_deleted,
                    "reply_count": 0,
                    "post_id": str(c.post_id),
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def soft_delete_comment(self, comment_id: UUID) -> None:
        result = await self.session.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.is_deleted = True
        await self.session.commit()

    async def restore_comment(self, comment_id: UUID) -> None:
        result = await self.session.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()
        if comment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        comment.is_deleted = False
        await self.session.commit()

    async def list_likes(self, page: int, limit: int, target_type: str | None = None) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        query = select(Like)
        if target_type:
            query = query.where(Like.target_type == target_type)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await self.session.execute(
            query.order_by(Like.created_at.desc()).offset((page - 1) * limit).limit(limit)
        )
        items = []
        for like in rows.scalars().all():
            user = await self.session.get(User, like.user_id)
            items.append(
                {
                    "id": str(like.id),
                    "user_id": str(like.user_id),
                    "user": {
                        "id": str(user.id),
                        "name": user.full_name,
                        "avatar_url": user.avatar_url,
                    }
                    if user
                    else None,
                    "target_type": like.target_type,
                    "target_id": str(like.target_id),
                    "created_at": like.created_at.isoformat() if like.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def delete_like(self, like_id: UUID) -> None:
        result = await self.session.execute(select(Like).where(Like.id == like_id))
        like = result.scalar_one_or_none()
        if like is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found")
        await self.session.delete(like)
        await self.session.commit()

    async def list_tournaments(self, page: int, limit: int, status_filter: str | None = None) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        query = select(Tournament)
        if status_filter:
            query = query.where(Tournament.status == status_filter)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await self.session.execute(
            query.order_by(Tournament.start_time.desc()).offset((page - 1) * limit).limit(limit)
        )
        items = []
        for t in rows.scalars().all():
            items.append(
                {
                    "id": str(t.id),
                    "parlor_id": str(t.parlor_id),
                    "title": t.title,
                    "game_type": t.game_type,
                    "format": t.format,
                    "start_time": t.start_time.isoformat() if t.start_time else None,
                    "end_time": t.end_time.isoformat() if t.end_time else None,
                    "total_slots": t.total_slots,
                    "booked_slots": t.booked_slots,
                    "entry_fee": float(t.entry_fee or 0),
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def update_tournament_status(self, tournament_id: UUID, new_status: str) -> dict:
        result = await self.session.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        tournament = result.scalar_one_or_none()
        if tournament is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
            )
        tournament.status = new_status
        await self.session.commit()
        await self.session.refresh(tournament)
        return {
            "id": str(tournament.id),
            "parlor_id": str(tournament.parlor_id),
            "title": tournament.title,
            "game_type": tournament.game_type,
            "format": tournament.format,
            "start_time": tournament.start_time.isoformat() if tournament.start_time else None,
            "end_time": tournament.end_time.isoformat() if tournament.end_time else None,
            "total_slots": tournament.total_slots,
            "booked_slots": tournament.booked_slots,
            "entry_fee": float(tournament.entry_fee or 0),
            "status": tournament.status,
            "created_at": tournament.created_at.isoformat() if tournament.created_at else None,
            "updated_at": tournament.updated_at.isoformat() if tournament.updated_at else None,
        }

    async def delete_tournament(self, tournament_id: UUID) -> None:
        result = await self.session.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        tournament = result.scalar_one_or_none()
        if tournament is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
            )
        tournament.status = "cancelled"
        await self.session.commit()

    async def list_tournament_bookings(
        self, page: int, limit: int, user_id: UUID | None = None
    ) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        query = select(Booking)
        if user_id:
            query = query.where(Booking.user_id == user_id)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await self.session.execute(
            query.order_by(Booking.created_at.desc()).offset((page - 1) * limit).limit(limit)
        )
        items = []
        for b in rows.scalars().all():
            items.append(
                {
                    "id": str(b.id),
                    "tournament_id": str(b.tournament_id),
                    "user_id": str(b.user_id),
                    "slot_number": b.slot_number,
                    "status": b.status,
                    "payment_status": getattr(b, "payment_status", "unknown"),
                    "booking_type": "tournament",
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def list_ratings(self, page: int, limit: int) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        total = await self.session.scalar(select(func.count()).select_from(ParlourRating)) or 0
        rows = await self.session.execute(
            select(ParlourRating)
            .order_by(ParlourRating.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = []
        for r in rows.scalars().all():
            user = await self.session.get(User, r.user_id)
            place = await self.session.get(GamingPlace, r.gaming_place_id)
            items.append(
                {
                    "id": str(r.id),
                    "user_id": str(r.user_id),
                    "parlor_id": str(r.gaming_place_id),
                    "user": {"id": str(user.id), "name": user.full_name} if user else None,
                    "parlor": {
                        "id": str(place.id),
                        "name": place.name,
                        "logo_url": resolve_media_url(place.image_url),
                        "is_verified": False,
                    }
                    if place
                    else None,
                    "rating": float(r.rating),
                    "review": r.review_text,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def delete_rating(self, rating_id: UUID) -> None:
        result = await self.session.execute(
            select(ParlourRating).where(ParlourRating.id == rating_id)
        )
        rating = result.scalar_one_or_none()
        if rating is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
        await self.session.delete(rating)
        await self.session.commit()

    async def list_geo_activity(self, page: int, limit: int) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        query = select(User).where(User.latitude.isnot(None), User.longitude.isnot(None))
        total = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await self.session.execute(
            query.order_by(User.location_updated_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = []
        for u in rows.scalars().all():
            items.append(
                {
                    "id": str(u.id),
                    "user_id": str(u.id),
                    "user": {"id": str(u.id), "name": u.full_name},
                    "latitude": u.latitude,
                    "longitude": u.longitude,
                    "post_preview": u.city,
                    "created_at": (
                        u.location_updated_at.isoformat()
                        if u.location_updated_at
                        else u.updated_at.isoformat()
                    ),
                }
            )
        return paginated(items, int(total), page, limit)

    async def broadcast(
        self, title: str, body: str, target: str, ntype: str, actor_id: UUID
    ) -> dict:
        query = select(User).where(User.is_active.is_(True))
        if target == "parlor_owners":
            query = query.where(User.role == UserRole.PARLOR_OWNER)
        elif target == "gamers":
            query = query.where(User.role == UserRole.USER)
        result = await self.session.execute(query.limit(5000))
        users = result.scalars().all()
        sent = 0
        for user in users:
            notif = Notification(
                user_id=user.id,
                type=ntype or "info",
                title=title,
                body=body,
                data={"source": "admin_broadcast", "target": target},
            )
            self.session.add(notif)
            sent += 1
        await self.session.commit()
        return {"sent_to": sent, "target": target, "type": ntype}

    async def list_stories(self, page: int, limit: int) -> dict:
        page, limit = max(1, page), min(max(1, limit), 100)
        total = await self.session.scalar(select(func.count()).select_from(Story)) or 0
        rows = await self.session.execute(
            select(Story)
            .order_by(Story.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = []
        for s in rows.scalars().all():
            user = await self.session.get(User, s.user_id)
            items.append(
                {
                    "id": str(s.id),
                    "user_id": str(s.user_id),
                    "user": {"id": str(user.id), "name": user.full_name} if user else None,
                    "media_url": s.media_url,
                    "media_type": s.media_type,
                    "caption": s.caption,
                    "privacy": s.privacy,
                    "view_count": s.view_count,
                    "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
            )
        return paginated(items, int(total), page, limit)

    async def delete_story(self, story_id: UUID) -> None:
        result = await self.session.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()
        if story is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
        await self.session.delete(story)
        await self.session.commit()

    async def update_offer(self, offer_id: UUID, data: dict) -> dict:
        result = await self.session.execute(
            select(ParlourOffer).where(ParlourOffer.id == offer_id)
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        for key, value in data.items():
            if value is not None and hasattr(offer, key):
                setattr(offer, key, value)
        await self.session.commit()
        await self.session.refresh(offer)
        return {
            "id": str(offer.id),
            "parlour_id": str(offer.parlour_id),
            "title": offer.title,
            "description": offer.description,
            "discount_type": "percentage" if offer.discount_percent else "flat",
            "discount_value": float(
                offer.discount_percent or offer.discount_amount or 0
            ),
            "valid_from": offer.valid_from.isoformat() if offer.valid_from else None,
            "valid_until": offer.valid_until.isoformat() if offer.valid_until else None,
            "is_active": offer.is_active,
            "usage_count": offer.current_uses or 0,
            "created_at": offer.created_at.isoformat() if offer.created_at else None,
        }

    async def delete_offer(self, offer_id: UUID) -> None:
        result = await self.session.execute(
            select(ParlourOffer).where(ParlourOffer.id == offer_id)
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        offer.is_active = False
        await self.session.commit()

    async def update_slot(self, slot_id: UUID, data: dict) -> dict:
        result = await self.session.execute(select(GamingSlot).where(GamingSlot.id == slot_id))
        slot = result.scalar_one_or_none()
        if slot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        for key, value in data.items():
            if value is not None and hasattr(slot, key):
                setattr(slot, key, value)
        await self.session.commit()
        await self.session.refresh(slot)
        return {
            "id": str(slot.id),
            "parlour_id": str(slot.parlour_id),
            "slot_date": slot.slot_date.isoformat() if slot.slot_date else None,
            "start_time": slot.start_time.isoformat() if slot.start_time else None,
            "end_time": slot.end_time.isoformat() if slot.end_time else None,
            "price_per_hour": float(slot.price_per_hour),
            "original_price": float(slot.original_price) if slot.original_price else None,
            "max_players": slot.max_players,
            "current_bookings": getattr(slot, "current_bookings", 0) or 0,
            "is_available": getattr(slot, "is_available", True),
            "game": getattr(slot, "game", None),
        }

    async def delete_slot(self, slot_id: UUID) -> None:
        result = await self.session.execute(select(GamingSlot).where(GamingSlot.id == slot_id))
        slot = result.scalar_one_or_none()
        if slot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        if hasattr(slot, "is_available"):
            slot.is_available = False
        else:
            await self.session.delete(slot)
        await self.session.commit()
