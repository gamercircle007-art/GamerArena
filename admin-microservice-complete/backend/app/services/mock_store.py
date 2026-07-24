"""In-memory platform data for the admin microservice (until shared DB is wired)."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


MOCK_USERS: list[dict[str, Any]] = [
    {
        "id": "u1", "name": "Manish Kumar", "username": "manishk", "email": "admin@gameconnect.in",
        "phone_number": "+919999999999", "role": "super_admin", "avatar_url": None,
        "is_active": True, "is_verified": True, "email_verified": True, "phone_verified": True,
        "latitude": None, "longitude": None, "city": "Bangalore", "country": "IN",
        "location_updated_at": None, "created_at": "2026-06-28T10:00:00Z", "updated_at": "2026-06-28T10:00:00Z",
        "bookings_count": 3, "likes_count": 45, "following_count": 12, "reviews_count": 2,
    },
    {
        "id": "u2", "name": "Priya Sharma", "username": "priyas", "email": "priya@gameconnect.in",
        "phone_number": "+919876543210", "role": "admin", "avatar_url": None,
        "is_active": True, "is_verified": True, "email_verified": True, "phone_verified": True,
        "latitude": None, "longitude": None, "city": "Bangalore", "country": "IN",
        "location_updated_at": None, "created_at": "2026-06-27T08:00:00Z", "updated_at": "2026-06-27T08:00:00Z",
        "bookings_count": 5, "likes_count": 22, "following_count": 8, "reviews_count": 4,
    },
    {
        "id": "u3", "name": "Rahul Gaming", "username": "rahulg", "email": "rahul@gmail.com",
        "phone_number": "+919111111111", "role": "user", "avatar_url": None,
        "is_active": True, "is_verified": True, "email_verified": False, "phone_verified": True,
        "latitude": None, "longitude": None, "city": "Mumbai", "country": "IN",
        "location_updated_at": None, "created_at": "2026-06-26T12:00:00Z", "updated_at": "2026-06-26T12:00:00Z",
        "bookings_count": 12, "likes_count": 120, "following_count": 34, "reviews_count": 5,
    },
    {
        "id": "u4", "name": "Anita Reddy", "username": "anitar", "email": "owner@cybercafe.in",
        "phone_number": "+919222222222", "role": "parlor_owner", "avatar_url": None,
        "is_active": True, "is_verified": True, "email_verified": True, "phone_verified": True,
        "latitude": None, "longitude": None, "city": "Bangalore", "country": "IN",
        "location_updated_at": None, "created_at": "2026-06-25T09:00:00Z", "updated_at": "2026-06-25T09:00:00Z",
        "parlor_name": "Arena Zone", "bookings_count": 0, "likes_count": 5, "following_count": 0, "reviews_count": 1,
    },
    {
        "id": "u6", "name": "Deepak Mehta", "username": "deepakm", "email": "deepak@spam.com",
        "phone_number": "+919555555555", "role": "user", "avatar_url": None,
        "is_active": False, "is_verified": False, "email_verified": False, "phone_verified": True,
        "latitude": None, "longitude": None, "city": "Delhi", "country": "IN",
        "location_updated_at": None, "created_at": "2026-06-20T11:00:00Z", "updated_at": "2026-06-21T09:00:00Z",
        "bookings_count": 0, "likes_count": 0, "following_count": 0, "reviews_count": 0,
    },
]

MOCK_PARLORS: list[dict[str, Any]] = [
    {
        "id": "p1", "owner_id": "u4", "name": "Arena Zone", "description": "Premium esports lounge",
        "logo_url": None, "address": "MG Road, Bangalore", "latitude": 12.9716, "longitude": 77.5946,
        "game_types": ["Valorant", "CS2", "FIFA"], "is_verified": True, "follower_count": 1250,
        "post_count": 48, "is_following": False, "rating": 4.6, "phone": "+919222222222",
        "website": None, "created_at": "2026-01-10T10:00:00Z", "updated_at": "2026-06-20T10:00:00Z",
    },
    {
        "id": "p2", "owner_id": "u5", "name": "GameHub Pro", "description": "Casual gaming café",
        "logo_url": None, "address": "Koramangala, Bangalore", "latitude": 12.9352, "longitude": 77.6245,
        "game_types": ["PUBG", "BGMI"], "is_verified": False, "follower_count": 340,
        "post_count": 12, "is_following": False, "rating": 4.1, "phone": "+919444444444",
        "website": None, "created_at": "2026-04-01T10:00:00Z", "updated_at": "2026-06-22T10:00:00Z",
    },
]

MOCK_BOOKINGS: list[dict[str, Any]] = [
    {
        "id": "b1", "tournament_id": "t1", "user_id": "u3", "slot_number": 3,
        "status": "confirmed", "payment_status": "paid", "booking_type": "tournament",
        "created_at": "2026-06-20T10:00:00Z",
        "tournament": {
            "id": "t1", "parlor_id": "p1", "title": "Valorant Weekend Cup", "game_type": "Valorant",
            "format": "5v5", "start_time": "2026-07-05T18:00:00Z", "end_time": "2026-07-05T22:00:00Z",
            "total_slots": 16, "booked_slots": 12, "entry_fee": 500, "status": "open",
            "created_at": "2026-06-01T10:00:00Z", "updated_at": "2026-06-01T10:00:00Z",
            "parlor": {"id": "p1", "name": "Arena Zone", "logo_url": None, "is_verified": True},
        },
    },
]

MOCK_DMS_ASSETS: list[dict[str, Any]] = [
    {
        "id": "asset-1",
        "cdn_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400",
        "thumbnail_url": None,
        "asset_type": "image",
        "original_filename": "gaming-setup.jpg",
        "file_size_label": "2.4 MB",
        "context": "post_media",
        "uploader_name": "Manish Kumar",
        "status": "active",
        "is_flagged": False,
        "created_at": "2026-07-01T10:00:00Z",
    },
    {
        "id": "asset-2",
        "cdn_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=400",
        "thumbnail_url": None,
        "asset_type": "image",
        "original_filename": "parlor-logo.png",
        "file_size_label": "512 KB",
        "context": "parlor_logo",
        "uploader_name": "Anita Reddy",
        "status": "active",
        "is_flagged": False,
        "created_at": "2026-07-02T08:00:00Z",
    },
    {
        "id": "asset-3",
        "cdn_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "thumbnail_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/ForBiggerBlazes.jpg",
        "asset_type": "video",
        "original_filename": "reel-highlight.mp4",
        "file_size_label": "18.2 MB",
        "context": "story",
        "uploader_name": "Rahul Gaming",
        "status": "active",
        "is_flagged": True,
        "created_at": "2026-07-02T14:00:00Z",
    },
]

MOCK_LIKES: list[dict[str, Any]] = [
    {
        "id": "l1", "user_id": "u3", "target_type": "post", "target_id": "post1",
        "target_preview": "New gaming rigs installed! RTX 4090 on every station.",
        "parlor_name": "Arena Zone", "created_at": "2026-06-22T10:00:00Z",
    },
]


class MockStore:
    def __init__(self) -> None:
        self.users = deepcopy(MOCK_USERS)
        self.parlors = deepcopy(MOCK_PARLORS)
        self.bookings = deepcopy(MOCK_BOOKINGS)
        self.likes = deepcopy(MOCK_LIKES)
        self.dms_assets = deepcopy(MOCK_DMS_ASSETS)

    def paginate(self, items: list, page: int, limit: int) -> dict:
        page = max(1, page)
        limit = min(max(1, limit), 100)
        total = len(items)
        start = (page - 1) * limit
        chunk = items[start : start + limit]
        return {
            "items": chunk,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": start + limit < total,
        }

    def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        items = list(self.users)
        if search:
            q = search.lower()
            items = [
                u for u in items
                if q in (u.get("name") or "").lower()
                or q in (u.get("username") or "").lower()
                or q in (u.get("email") or "").lower()
                or q in (u.get("phone_number") or "")
            ]
        if role:
            items = [u for u in items if u.get("role") == role]
        if is_active is not None:
            items = [u for u in items if u.get("is_active") == is_active]
        return self.paginate(items, page, limit)

    def get_user(self, user_id: str) -> dict | None:
        return next((u for u in self.users if u["id"] == user_id), None)

    def update_user(self, user_id: str, data: dict) -> dict | None:
        user = self.get_user(user_id)
        if not user:
            return None
        user.update(data)
        user["updated_at"] = _now()
        return user

    def delete_user(self, user_id: str) -> bool:
        before = len(self.users)
        self.users = [u for u in self.users if u["id"] != user_id]
        return len(self.users) < before

    def stats(self) -> dict:
        return {
            "users": len(self.users),
            "parlors": len(self.parlors),
            "tournaments": 2,
            "bookings": len(self.bookings),
            "posts": 48,
            "revenue": 125000,
            "new_users_today": 2,
            "pending_verification": sum(1 for p in self.parlors if not p.get("is_verified")),
        }

    def analytics(self, period: str = "30d") -> dict:
        days = 7 if period == "7d" else 90 if period == "90d" else 30
        return {
            "period": period,
            "user_growth": [{"date": f"2026-06-{i:02d}", "count": 5 + i} for i in range(1, days + 1)],
            "bookings_per_day": [{"date": f"2026-06-{i:02d}", "count": 3 + i % 5} for i in range(1, days + 1)],
            "posts_per_day": [{"date": f"2026-06-{i:02d}", "count": 2 + i % 3} for i in range(1, days + 1)],
            "game_distribution": [
                {"label": "Valorant", "value": 35},
                {"label": "CS2", "value": 25},
                {"label": "BGMI", "value": 20},
                {"label": "FIFA", "value": 12},
            ],
            "top_parlors": [
                {"parlor_id": "p1", "parlor_name": "Arena Zone", "bookings_count": 186},
                {"parlor_id": "p2", "parlor_name": "GameHub Pro", "bookings_count": 98},
            ],
            "total_users": len(self.users),
            "new_users": 42,
            "total_bookings": 320,
            "revenue": 125000,
        }

    def list_bookings(self, user_id: str | None = None, page: int = 1, limit: int = 20) -> dict:
        items = self.bookings
        if user_id:
            items = [b for b in items if b.get("user_id") == user_id]
        return self.paginate(items, page, limit)

    def list_likes(self, user_id: str | None = None, page: int = 1, limit: int = 20) -> dict:
        items = [l for l in self.likes if l.get("target_type") == "post"]
        if user_id:
            items = [l for l in items if l.get("user_id") == user_id]
        return self.paginate(items, page, limit)

    def get_parlor(self, parlor_id: str) -> dict | None:
        return next((p for p in self.parlors if p["id"] == parlor_id), None)

    def verify_parlor(self, parlor_id: str, is_verified: bool) -> dict | None:
        parlor = self.get_parlor(parlor_id)
        if not parlor:
            return None
        parlor["is_verified"] = is_verified
        parlor["updated_at"] = _now()
        return parlor

    def delete_parlor(self, parlor_id: str) -> bool:
        parlor = self.get_parlor(parlor_id)
        if not parlor:
            return False
        parlor["is_deleted"] = True
        parlor["is_active"] = False
        parlor["updated_at"] = _now()
        return True

    def create_parlor(self, data: dict) -> dict:
        parlor = {
            "id": f"p-{len(self.parlors) + 1}",
            "owner_id": data.get("owner_id"),
            "name": data.get("name") or "New Parlor",
            "description": data.get("description"),
            "logo_url": data.get("image_url") or data.get("logo_url"),
            "address": data.get("address"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "game_types": data.get("game_types") or [],
            "is_verified": bool(data.get("is_verified", False)),
            "follower_count": 0,
            "post_count": 0,
            "is_following": False,
            "rating": None,
            "phone": data.get("phone"),
            "website": data.get("website"),
            "is_active": bool(data.get("is_active", True)),
            "is_deleted": False,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.parlors.insert(0, parlor)
        return parlor

    def update_parlor(self, parlor_id: str, data: dict) -> dict | None:
        parlor = self.get_parlor(parlor_id)
        if not parlor:
            return None
        for key, value in data.items():
            if key == "image_url":
                parlor["logo_url"] = value
            elif key in parlor or key in (
                "owner_id", "name", "address", "phone", "website",
                "latitude", "longitude", "game_types", "is_verified",
                "is_active", "is_deleted", "description",
            ):
                parlor[key] = value
        parlor["updated_at"] = _now()
        return parlor

    def assign_owner(self, parlor_id: str, owner_id: str | None) -> dict | None:
        return self.update_parlor(parlor_id, {"owner_id": owner_id})

    def restore_parlor(self, parlor_id: str) -> dict | None:
        return self.update_parlor(parlor_id, {"is_deleted": False, "is_active": True})

    def list_parlors(
        self,
        page: int = 1,
        limit: int = 20,
        is_verified: bool | None = None,
        search: str | None = None,
    ) -> dict:
        items = [p for p in self.parlors if not p.get("is_deleted")]
        if is_verified is not None:
            items = [p for p in items if p.get("is_verified") == is_verified]
        if search:
            q = search.lower()
            items = [
                p for p in items
                if q in (p.get("name") or "").lower()
                or q in (p.get("address") or "").lower()
                or any(q in g.lower() for g in p.get("game_types", []))
            ]
        return self.paginate(items, page, limit)

    def list_dms_assets(
        self,
        page: int = 1,
        limit: int = 20,
        asset_type: str | None = None,
        search: str | None = None,
    ) -> dict:
        items = list(self.dms_assets)
        if asset_type:
            items = [a for a in items if a.get("asset_type") == asset_type]
        if search:
            q = search.lower()
            items = [
                a for a in items
                if q in (a.get("original_filename") or "").lower()
                or q in (a.get("context") or "").lower()
            ]
        return self.paginate(items, page, limit)

    def dms_stats(self) -> dict:
        total = len(self.dms_assets)
        flagged = sum(1 for a in self.dms_assets if a.get("is_flagged"))
        by_type: dict[str, int] = {}
        for a in self.dms_assets:
            t = a.get("asset_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        by_context: dict[str, int] = {}
        for a in self.dms_assets:
            c = a.get("context", "unknown")
            by_context[c] = by_context.get(c, 0) + 1
        return {
            "total_count": total,
            "total_size_bytes": 24_500_000,
            "total_size_label": "23.4 MB",
            "by_type": by_type,
            "by_context": by_context,
            "flagged_count": flagged,
        }

    def list_dms_orphans(self, page: int = 1, limit: int = 20) -> dict:
        return self.paginate([], page, limit)

    def delete_dms_asset(self, asset_id: str) -> bool:
        before = len(self.dms_assets)
        self.dms_assets = [a for a in self.dms_assets if a["id"] != asset_id]
        return len(self.dms_assets) < before

    def flag_dms_asset(self, asset_id: str, is_flagged: bool, reason: str | None = None) -> dict | None:
        asset = next((a for a in self.dms_assets if a["id"] == asset_id), None)
        if not asset:
            return None
        asset["is_flagged"] = is_flagged
        asset["status"] = "flagged" if is_flagged else "active"
        return asset

    def bulk_delete_dms(self, asset_ids: list[str]) -> dict:
        deleted = 0
        for aid in asset_ids:
            if self.delete_dms_asset(str(aid)):
                deleted += 1
        return {"deleted": deleted, "requested": len(asset_ids)}


store = MockStore()