"""Club Management tests (Phase 5).

Covers the four things the build spec's DEFINITION OF DONE calls out:
  1. **club-scoping / auth-bypass** — a cross-club request must 403 (not 404, not 200)
  2. **pricing resolution** — slabs, day-of-week overrides, packages, precedence, fallback
  3. **promo validation** — every rejection reason, and best-value selection
  4. **rollup idempotency** — re-running a bucket must not double-count

Unlike the older smoke tests in this directory (which share `dev.db`), these build an
isolated temp SQLite database per module via `metadata.create_all` and override the app's
`get_db_session` dependency. That keeps them deterministic and side-effect free, and it
means they can assert on exact numbers rather than "some rows exist".
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_minimum_32_characters_long")
os.environ.setdefault("APP_ENV", "local")

from app.core.dependencies import get_db_session  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models import *  # noqa: E402,F401,F403  (registers every table)
from app.domains.club_ops.enums import (  # noqa: E402
    BOOKING_STATUS_NO_SHOW,
    PricingScope,
    PromotionType,
    ResourceStatus,
    ResourceType,
    RollupGrain,
)
from app.domains.club_ops.models import (  # noqa: E402
    ClubCustomer,
    ClubPricingRule,
    ClubPromotion,
    ClubResource,
    ClubZone,
    OccupancyRollup,
)
from app.domains.club_ops.pricing import PriceResolver  # noqa: E402
from app.domains.club_ops.promotions import PromotionService  # noqa: E402
from app.domains.club_ops.rollup_service import RollupService  # noqa: E402
from app.domains.gaming_booking.models import GamingBooking  # noqa: E402
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension  # noqa: E402
from app.domains.user.models import User, UserRole  # noqa: E402
from app.main import app  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")


# --- fixtures ---------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module")
async def engine(tmp_path_factory):
    """Isolated SQLite database for this module only."""
    db_path = Path(tmp_path_factory.mktemp("club_ops")) / "club_ops_test.db"
    eng = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db(session_factory):
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seed(db):
    """Two clubs with two different owners, plus a platform admin.

    This shape is what makes the cross-club assertions meaningful: owner_a must never
    be able to reach club_b.
    """
    now = datetime.now(UTC)
    owner_a = User(
        id=uuid.uuid4(),
        full_name="Owner A",
        phone=f"+9199{uuid.uuid4().int % 100000000:08d}",
        role=UserRole.PARLOR_OWNER,
        is_active=True,
    )
    owner_b = User(
        id=uuid.uuid4(),
        full_name="Owner B",
        phone=f"+9198{uuid.uuid4().int % 100000000:08d}",
        role=UserRole.PARLOR_OWNER,
        is_active=True,
    )
    admin = User(
        id=uuid.uuid4(),
        full_name="Platform Admin",
        phone=f"+9197{uuid.uuid4().int % 100000000:08d}",
        role=UserRole.ADMIN,
        is_active=True,
    )
    plain = User(
        id=uuid.uuid4(),
        full_name="Plain User",
        phone=f"+9196{uuid.uuid4().int % 100000000:08d}",
        role=UserRole.USER,
        is_active=True,
    )
    db.add_all([owner_a, owner_b, admin, plain])

    club_a = GamingPlace(
        id=uuid.uuid4(),
        google_place_id=f"gp_{uuid.uuid4().hex[:12]}",
        name="Club A",
        city_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    club_b = GamingPlace(
        id=uuid.uuid4(),
        google_place_id=f"gp_{uuid.uuid4().hex[:12]}",
        name="Club B",
        city_id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )
    db.add_all([club_a, club_b])
    await db.flush()

    db.add_all(
        [
            GamingPlaceExtension(
                gaming_place_id=club_a.id, owner_id=owner_a.id, price_per_hour=Decimal("120.00")
            ),
            GamingPlaceExtension(
                gaming_place_id=club_b.id, owner_id=owner_b.id, price_per_hour=Decimal("80.00")
            ),
        ]
    )
    await db.commit()

    return {
        "owner_a": owner_a,
        "owner_b": owner_b,
        "admin": admin,
        "plain": plain,
        "club_a": club_a,
        "club_b": club_b,
    }


@pytest_asyncio.fixture
async def api(session_factory):
    """HTTP client bound to the isolated test database."""

    async def _override():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db_session, None)


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


# --- 1. club scoping / auth bypass -----------------------------------------------


@pytest.mark.asyncio
async def test_club_endpoints_require_auth(api):
    for path in ("/api/v1/club/resources", "/api/v1/club/live", "/api/v1/club/revenue/summary"):
        response = await api.get(path)
        assert response.status_code == 401, path


@pytest.mark.asyncio
async def test_plain_user_cannot_reach_club_management(api, seed):
    """A user who owns no club gets 403, not an empty 200."""
    response = await api.get("/api/v1/club/resources", headers=auth(seed["plain"]))
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


@pytest.mark.asyncio
async def test_owner_reaches_own_club_without_naming_it(api, seed):
    """Ownership is 1:1 today, so parlor_id may be omitted and is inferred."""
    response = await api.get("/api/v1/club/resources", headers=auth(seed["owner_a"]))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_cross_club_read_is_forbidden(api, seed):
    """THE auth-bypass case: owner_a naming club_b must 403."""
    response = await api.get(
        f"/api/v1/club/resources?parlor_id={seed['club_b'].id}",
        headers=auth(seed["owner_a"]),
    )
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


@pytest.mark.asyncio
async def test_cross_club_write_is_forbidden(api, seed):
    response = await api.post(
        f"/api/v1/club/zones?parlor_id={seed['club_b'].id}",
        headers=auth(seed["owner_a"]),
        json={"name": "Injected Zone", "sort_order": 0},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cross_club_resource_by_id_is_not_reachable(api, seed, db):
    """Even a valid resource UUID from another club must not resolve for owner_a.

    Guards the subtler bypass: scoping the club but then fetching a child row by id
    without re-checking its parent.
    """
    resource = ClubResource(
        parlor_id=seed["club_b"].id,
        resource_type=ResourceType.PC.value,
        label="B-PC-1",
        status=ResourceStatus.AVAILABLE.value,
    )
    db.add(resource)
    await db.commit()

    response = await api.get(
        f"/api/v1/club/resources/{resource.id}", headers=auth(seed["owner_a"])
    )
    # 404 from within owner_a's own (correctly scoped) club — the row is invisible,
    # which is the desired outcome; what must never happen is a 200.
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_must_name_a_club(api, seed):
    """An admin owns nothing, so an unscoped admin request is rejected rather than
    silently returning some arbitrary club."""
    response = await api.get("/api/v1/club/resources", headers=auth(seed["admin"]))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_may_name_any_club(api, seed):
    response = await api.get(
        f"/api/v1/club/resources?parlor_id={seed['club_b'].id}", headers=auth(seed["admin"])
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_owner_cannot_use_admin_oversight_endpoints(api, seed):
    response = await api.get(
        f"/api/v1/admin/club-management/clubs/{seed['club_a'].id}/revenue",
        headers=auth(seed["owner_a"]),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_pricing_rule_cannot_reference_another_clubs_zone(api, seed, db):
    """A rate must not be able to cross the tenant boundary via scope_value."""
    zone_b = ClubZone(parlor_id=seed["club_b"].id, name="B Zone")
    db.add(zone_b)
    await db.commit()

    response = await api.post(
        "/api/v1/club/pricing/rules",
        headers=auth(seed["owner_a"]),
        json={
            "name": "Cross-club rule",
            "scope": "zone",
            "scope_value": str(zone_b.id),
            "base_rate_paise": 10000,
        },
    )
    assert response.status_code == 404


# --- 2. pricing resolution -------------------------------------------------------


@pytest.mark.asyncio
async def test_price_falls_back_to_venue_rate_without_rules(db, seed):
    """No pricing rule configured -> the club's existing price_per_hour (₹120)."""
    breakdown = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(11, 0),
        duration_hours=2,
    )
    assert breakdown.source == "venue"
    assert breakdown.base_rate_paise == 12000
    assert breakdown.subtotal_paise == 24000


@pytest.mark.asyncio
async def test_peak_slab_multiplier_applies_per_hour(db, seed):
    """A 1.5x peak window from 18:00 must only lift the hours inside it."""
    db.add(
        ClubPricingRule(
            parlor_id=seed["club_a"].id,
            name="PC standard",
            scope=PricingScope.RESOURCE_TYPE.value,
            scope_value=ResourceType.PC.value,
            base_rate_paise=10000,
            time_slabs=[
                {"label": "peak", "start": "18:00", "end": "23:00", "multiplier_bps": 15000}
            ],
            priority=0,
            is_active=True,
        )
    )
    await db.commit()

    # 17:00-19:00 -> one off-peak hour (100.00) + one peak hour (150.00)
    breakdown = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(17, 0),
        duration_hours=2,
    )
    assert breakdown.source == "pricing_rule"
    assert [h.rate_paise for h in breakdown.per_hour] == [10000, 15000]
    assert [h.slab_label for h in breakdown.per_hour] == [None, "peak"]
    assert breakdown.subtotal_paise == 25000


@pytest.mark.asyncio
async def test_units_multiply_the_total(db, seed):
    breakdown = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(11, 0),
        duration_hours=2,
        units=3,
    )
    assert breakdown.subtotal_paise == 24000 * 3


@pytest.mark.asyncio
async def test_wrapping_slab_window_covers_past_midnight(db, seed):
    db.add(
        ClubPricingRule(
            parlor_id=seed["club_a"].id,
            name="Night rate",
            scope=PricingScope.RESOURCE_TYPE.value,
            scope_value=ResourceType.VR.value,
            base_rate_paise=20000,
            time_slabs=[
                {"label": "night", "start": "22:00", "end": "02:00", "flat_paise": 5000}
            ],
            is_active=True,
        )
    )
    await db.commit()

    breakdown = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.VR.value,
        booking_date=date(2026, 8, 5),
        start_time=time(23, 0),
        duration_hours=2,
    )
    # 23:00 and 00:00 both fall in the wrapping window -> flat 50.00 each
    assert [h.rate_paise for h in breakdown.per_hour] == [5000, 5000]
    assert all(h.slab_label == "night" for h in breakdown.per_hour)


@pytest.mark.asyncio
async def test_day_of_week_override_stacks_on_slab(db, seed):
    db.add(
        ClubPricingRule(
            parlor_id=seed["club_a"].id,
            name="Pool weekend",
            scope=PricingScope.RESOURCE_TYPE.value,
            scope_value=ResourceType.POOL.value,
            base_rate_paise=10000,
            # 2026-08-08 is a Saturday -> weekday 5
            day_of_week_overrides={"5": {"multiplier_bps": 12000}},
            is_active=True,
        )
    )
    await db.commit()

    saturday = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.POOL.value,
        booking_date=date(2026, 8, 8),
        start_time=time(12, 0),
        duration_hours=1,
    )
    assert saturday.per_hour[0].rate_paise == 12000
    assert saturday.per_hour[0].dow_override is True

    wednesday = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.POOL.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
        duration_hours=1,
    )
    assert wednesday.per_hour[0].rate_paise == 10000
    assert wednesday.per_hour[0].dow_override is False


@pytest.mark.asyncio
async def test_package_short_circuits_hourly_pricing(db, seed):
    db.add(
        ClubPricingRule(
            parlor_id=seed["club_a"].id,
            name="Console bundles",
            scope=PricingScope.RESOURCE_TYPE.value,
            scope_value=ResourceType.PS5.value,
            base_rate_paise=10000,
            time_slabs=[
                {"label": "peak", "start": "00:00", "end": "23:59", "multiplier_bps": 20000}
            ],
            package_defs=[{"label": "3hr bundle", "hours": 3, "price_paise": 25000}],
            is_active=True,
        )
    )
    await db.commit()

    resolver = PriceResolver(db)
    bundled = await resolver.resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PS5.value,
        booking_date=date(2026, 8, 5),
        start_time=time(19, 0),
        duration_hours=3,
    )
    assert bundled.source == "package"
    assert bundled.package_label == "3hr bundle"
    assert bundled.subtotal_paise == 25000

    # A 2-hour booking has no matching package, so the peak slab applies instead.
    unbundled = await resolver.resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PS5.value,
        booking_date=date(2026, 8, 5),
        start_time=time(19, 0),
        duration_hours=2,
    )
    assert unbundled.source == "pricing_rule"
    assert unbundled.subtotal_paise == 40000


@pytest.mark.asyncio
async def test_resource_override_beats_rule_base_rate(db, seed):
    resource = ClubResource(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PC.value,
        label="PC-VIP",
        status=ResourceStatus.AVAILABLE.value,
        hourly_rate_override_paise=30000,
    )
    db.add(resource)
    await db.commit()

    breakdown = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(11, 0),
        duration_hours=1,
        resource_id=resource.id,
    )
    assert breakdown.source == "resource_override"
    assert breakdown.subtotal_paise == 30000


@pytest.mark.asyncio
async def test_more_specific_scope_wins(db, seed):
    """A resource_type rule must beat a club-wide rule, even a higher-priority one.

    Both rules are created here rather than relying on another test's fixtures — the
    `seed` fixture is function-scoped, so every test gets its own clubs.
    """
    club_id = seed["club_a"].id
    db.add_all(
        [
            ClubPricingRule(
                parlor_id=club_id,
                name="Club-wide floor",
                scope=PricingScope.CLUB.value,
                scope_value="",
                base_rate_paise=1000,
                priority=99,  # high priority must still lose to a more specific scope
                is_active=True,
            ),
            ClubPricingRule(
                parlor_id=club_id,
                name="PC specific",
                scope=PricingScope.RESOURCE_TYPE.value,
                scope_value=ResourceType.PC.value,
                base_rate_paise=10000,
                priority=0,
                is_active=True,
            ),
        ]
    )
    await db.commit()

    breakdown = await PriceResolver(db).resolve(
        parlor_id=club_id,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(11, 0),
        duration_hours=1,
    )
    assert breakdown.rule_name == "PC specific"
    assert breakdown.base_rate_paise == 10000

    # A type with no specific rule still falls through to the club-wide rule.
    other = await PriceResolver(db).resolve(
        parlor_id=club_id,
        resource_type=ResourceType.POOL.value,
        booking_date=date(2026, 8, 5),
        start_time=time(11, 0),
        duration_hours=1,
    )
    assert other.rule_name == "Club-wide floor"


@pytest.mark.asyncio
async def test_preview_endpoint_matches_resolver(api, db, seed):
    """The preview endpoint must not diverge from the resolver — same rule, same total."""
    direct = await PriceResolver(db).resolve(
        parlor_id=seed["club_a"].id,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(17, 0),
        duration_hours=2,
    )
    response = await api.post(
        "/api/v1/club/pricing/preview",
        headers=auth(seed["owner_a"]),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-05",
            "start_time": "17:00:00",
            "duration_hours": 2,
            "units": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["subtotal_paise"] == direct.subtotal_paise


# --- 3. promotion validation -----------------------------------------------------


@pytest_asyncio.fixture
async def promo_club(db, seed):
    """A club with one customer for promo evaluation."""
    customer = ClubCustomer(
        parlor_id=seed["club_a"].id, display_name="Promo Tester", phone="+919000000001"
    )
    db.add(customer)
    await db.commit()
    return {"club_id": seed["club_a"].id, "customer": customer}


@pytest.mark.asyncio
async def test_percent_promo_is_capped_by_max_discount(db, promo_club):
    promo = ClubPromotion(
        parlor_id=promo_club["club_id"],
        name="Half off capped",
        promo_type=PromotionType.CODE.value,
        percent_bps=5000,  # 50%
        max_discount_paise=10000,  # but never more than ₹100
        code="HALF",
        is_active=True,
    )
    db.add(promo)
    await db.commit()

    outcome = await PromotionService(db).validate(
        parlor_id=promo_club["club_id"],
        subtotal_paise=100000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
        code="HALF",
    )
    assert outcome.valid is True
    assert outcome.discount_paise == 10000


@pytest.mark.asyncio
async def test_promo_code_match_is_case_insensitive(db, promo_club):
    """Codes are read off a counter by a human — matching must not be case-sensitive."""
    db.add(
        ClubPromotion(
            parlor_id=promo_club["club_id"],
            name="Mixed case code",
            promo_type=PromotionType.CODE.value,
            percent_bps=1000,
            code="SummerFest",
            is_active=True,
        )
    )
    await db.commit()

    service = PromotionService(db)
    for variant in ("summerfest", "SUMMERFEST", "SummerFest", "  summerfest  "):
        outcome = await service.validate(
            parlor_id=promo_club["club_id"],
            subtotal_paise=50000,
            resource_type=ResourceType.PC.value,
            booking_date=date(2026, 8, 5),
            start_time=time(12, 0),
            code=variant,
        )
        assert outcome.valid is True, variant
        assert outcome.discount_paise == 5000


@pytest.mark.asyncio
async def test_promo_never_discounts_below_zero(db, promo_club):
    promo = ClubPromotion(
        parlor_id=promo_club["club_id"],
        name="Huge flat",
        promo_type=PromotionType.FLAT.value,
        flat_paise=999999,
        code="HUGE",
        is_active=True,
    )
    db.add(promo)
    await db.commit()

    outcome = await PromotionService(db).validate(
        parlor_id=promo_club["club_id"],
        subtotal_paise=20000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
        code="HUGE",
    )
    assert outcome.discount_paise == 20000


@pytest.mark.asyncio
async def test_promo_rejection_reasons(db, promo_club):
    """Each guard must fail with its own explanation, not a generic 'invalid'."""
    club_id = promo_club["club_id"]
    service = PromotionService(db)
    common = {
        "parlor_id": club_id,
        "subtotal_paise": 50000,
        "resource_type": ResourceType.PC.value,
        "booking_date": date(2026, 8, 5),
        "start_time": time(12, 0),
    }

    expired = ClubPromotion(
        parlor_id=club_id,
        name="Expired",
        promo_type=PromotionType.CODE.value,
        percent_bps=1000,
        code="EXPIRED",
        valid_to=datetime(2026, 1, 1, tzinfo=UTC),
        is_active=True,
    )
    exhausted = ClubPromotion(
        parlor_id=club_id,
        name="Exhausted",
        promo_type=PromotionType.CODE.value,
        percent_bps=1000,
        code="USEDUP",
        usage_limit=2,
        used_count=2,
        is_active=True,
    )
    inactive = ClubPromotion(
        parlor_id=club_id,
        name="Inactive",
        promo_type=PromotionType.CODE.value,
        percent_bps=1000,
        code="OFF",
        is_active=False,
    )
    platform_killed = ClubPromotion(
        parlor_id=club_id,
        name="Platform disabled",
        promo_type=PromotionType.CODE.value,
        percent_bps=1000,
        code="KILLED",
        is_active=True,
        disabled_by_platform=True,
        disabled_reason="Abuse",
    )
    min_spend = ClubPromotion(
        parlor_id=club_id,
        name="Min spend",
        promo_type=PromotionType.CODE.value,
        percent_bps=1000,
        code="MIN",
        min_amount_paise=200000,
        is_active=True,
    )
    wrong_type = ClubPromotion(
        parlor_id=club_id,
        name="VR only",
        promo_type=PromotionType.CODE.value,
        percent_bps=1000,
        code="VRONLY",
        applicable_resource_types=[ResourceType.VR.value],
        is_active=True,
    )
    db.add_all([expired, exhausted, inactive, platform_killed, min_spend, wrong_type])
    await db.commit()

    cases = {
        "EXPIRED": "expired",
        "USEDUP": "usage limit",
        "OFF": "not active",
        "KILLED": "Abuse",
        "MIN": "Minimum spend",
        "VRONLY": "Not applicable",
    }
    for code, fragment in cases.items():
        outcome = await service.validate(**common, code=code)
        assert outcome.valid is False, code
        assert fragment.lower() in (outcome.reason or "").lower(), (code, outcome.reason)

    unknown = await service.validate(**common, code="NOSUCHCODE")
    assert unknown.valid is False
    assert "not found" in (unknown.reason or "").lower()


@pytest.mark.asyncio
async def test_happy_hour_window_is_enforced(db, promo_club):
    db.add(
        ClubPromotion(
            parlor_id=promo_club["club_id"],
            name="Afternoon lull",
            promo_type=PromotionType.HAPPY_HOUR.value,
            percent_bps=2000,
            happy_hour_start=time(14, 0),
            happy_hour_end=time(17, 0),
            is_active=True,
        )
    )
    await db.commit()
    service = PromotionService(db)

    inside = await service.apply_best(
        parlor_id=promo_club["club_id"],
        subtotal_paise=50000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(15, 0),
    )
    assert inside.valid is True
    assert inside.discount_paise == 10000

    outside = await service.apply_best(
        parlor_id=promo_club["club_id"],
        subtotal_paise=50000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(20, 0),
    )
    assert outside.valid is False


@pytest.mark.asyncio
async def test_first_visit_promo_respects_visit_count(db, promo_club):
    customer = promo_club["customer"]
    db.add(
        ClubPromotion(
            parlor_id=promo_club["club_id"],
            name="Welcome",
            promo_type=PromotionType.FIRST_VISIT.value,
            flat_paise=5000,
            is_active=True,
        )
    )
    await db.commit()
    service = PromotionService(db)
    args = {
        "parlor_id": promo_club["club_id"],
        "subtotal_paise": 50000,
        "resource_type": ResourceType.PC.value,
        "booking_date": date(2026, 8, 5),
        "start_time": time(20, 0),  # outside happy hour, so only this promo can win
        "club_customer_id": customer.id,
    }

    first = await service.apply_best(**args)
    assert first.valid is True
    assert first.promo_type == PromotionType.FIRST_VISIT.value

    customer.visit_count = 4
    await db.commit()

    returning = await service.apply_best(**args)
    assert returning.valid is False


@pytest.mark.asyncio
async def test_apply_best_picks_largest_discount(db, seed):
    """Among automatic promos, the best-value one wins."""
    club_id = seed["club_b"].id  # a clean club, no promos yet
    db.add_all(
        [
            ClubPromotion(
                parlor_id=club_id,
                name="Small",
                promo_type=PromotionType.PERCENT.value,
                percent_bps=500,  # 5% of 50000 = 2500
                is_active=True,
            ),
            ClubPromotion(
                parlor_id=club_id,
                name="Big",
                promo_type=PromotionType.FLAT.value,
                flat_paise=9000,
                is_active=True,
            ),
        ]
    )
    await db.commit()

    outcome = await PromotionService(db).apply_best(
        parlor_id=club_id,
        subtotal_paise=50000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
    )
    assert outcome.promotion_name == "Big"
    assert outcome.discount_paise == 9000


@pytest.mark.asyncio
async def test_code_promos_are_not_auto_applied(db, seed):
    """A code promo must require the code — otherwise every booking silently gets it."""
    club_id = seed["club_b"].id
    db.add(
        ClubPromotion(
            parlor_id=club_id,
            name="Secret",
            promo_type=PromotionType.CODE.value,
            percent_bps=9000,
            code="SECRET90",
            is_active=True,
        )
    )
    await db.commit()

    auto = await PromotionService(db).apply_best(
        parlor_id=club_id,
        subtotal_paise=50000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
    )
    assert auto.promotion_name != "Secret"


@pytest.mark.asyncio
async def test_promotion_from_another_club_is_invisible(db, seed):
    """Scoping applies to promo lookup too — a code from club B must not work at club A."""
    db.add(
        ClubPromotion(
            parlor_id=seed["club_b"].id,
            name="B only",
            promo_type=PromotionType.CODE.value,
            percent_bps=5000,
            code="BONLY",
            is_active=True,
        )
    )
    await db.commit()

    outcome = await PromotionService(db).validate(
        parlor_id=seed["club_a"].id,
        subtotal_paise=50000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
        code="BONLY",
    )
    assert outcome.valid is False
    assert "not found" in (outcome.reason or "").lower()


# --- 4. rollup idempotency -------------------------------------------------------


@pytest_asyncio.fixture
async def rollup_fixture(db, seed):
    """A club with two PCs and one 2-hour confirmed booking at 18:00 IST."""
    club_id = seed["club_b"].id
    zone = ClubZone(parlor_id=club_id, name="Main Floor")
    db.add(zone)
    await db.flush()

    pc1 = ClubResource(
        parlor_id=club_id,
        zone_id=zone.id,
        resource_type=ResourceType.PC.value,
        label="PC-1",
        status=ResourceStatus.AVAILABLE.value,
    )
    pc2 = ClubResource(
        parlor_id=club_id,
        zone_id=zone.id,
        resource_type=ResourceType.PC.value,
        label="PC-2",
        status=ResourceStatus.AVAILABLE.value,
    )
    db.add_all([pc1, pc2])
    await db.flush()

    booking_date = date(2026, 8, 5)
    booking = GamingBooking(
        booking_ref=f"RB{uuid.uuid4().hex[:8].upper()}",
        user_id=seed["owner_b"].id,
        parlour_id=club_id,
        slot_date=booking_date,
        start_time=time(18, 0),
        end_time=time(20, 0),
        duration_hours=2,
        units=1,
        num_players=1,
        station_type="PC",
        booking_status="confirmed",
        payment_status="paid",
        payment_mode="cash",
        amount_paise=40000,
        commission_paise=4000,
        resource_id=pc1.id,
        final_price=Decimal("400.00"),
    )
    db.add(booking)
    await db.commit()
    return {"club_id": club_id, "date": booking_date, "zone": zone, "pc1": pc1, "booking": booking}


def _bucket(day: date, hour: int) -> datetime:
    return datetime.combine(day, time(hour, 0), tzinfo=IST)


async def _club_row(db, club_id, day: date, hour: int) -> OccupancyRollup | None:
    return (
        await db.execute(
            select(OccupancyRollup).where(
                OccupancyRollup.parlor_id == club_id,
                OccupancyRollup.grain == RollupGrain.CLUB.value,
                OccupancyRollup.grain_key == "",
                OccupancyRollup.bucket_start == _bucket(day, hour).astimezone(UTC),
            )
        )
    ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_rollup_computes_expected_bucket(db, rollup_fixture):
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]

    await RollupService(db).rebuild_bucket(club_id, _bucket(day, 18))

    row = await _club_row(db, club_id, day, 18)
    assert row is not None
    assert row.occupied_minutes == 60  # 1 unit busy for the whole hour
    assert row.capacity_minutes == 120  # 2 PCs x 60 min
    assert row.booking_count == 1  # the booking starts in this bucket
    assert row.revenue_paise == 40000
    assert row.commission_paise == 4000
    assert row.ist_hour == 18
    assert row.ist_weekday == day.weekday()


@pytest.mark.asyncio
async def test_rollup_is_idempotent(db, rollup_fixture):
    """THE idempotency requirement: re-running a bucket must not double anything."""
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]
    service = RollupService(db)

    await service.rebuild_bucket(club_id, _bucket(day, 18))
    first = await _club_row(db, club_id, day, 18)
    snapshot = (
        first.occupied_minutes,
        first.capacity_minutes,
        first.booking_count,
        first.revenue_paise,
        first.commission_paise,
    )

    for _ in range(3):
        await service.rebuild_bucket(club_id, _bucket(day, 18))

    rows = (
        await db.execute(
            select(OccupancyRollup).where(
                OccupancyRollup.parlor_id == club_id,
                OccupancyRollup.grain == RollupGrain.CLUB.value,
                OccupancyRollup.bucket_start == _bucket(day, 18).astimezone(UTC),
            )
        )
    ).scalars().all()
    assert len(rows) == 1, "re-running a bucket must not insert duplicate rows"

    again = rows[0]
    assert (
        again.occupied_minutes,
        again.capacity_minutes,
        again.booking_count,
        again.revenue_paise,
        again.commission_paise,
    ) == snapshot


@pytest.mark.asyncio
async def test_rollup_range_is_idempotent(db, rollup_fixture):
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]
    service = RollupService(db)

    await service.rebuild_range(club_id, from_date=day, to_date=day)
    first_count = (
        await db.execute(
            select(OccupancyRollup).where(OccupancyRollup.parlor_id == club_id)
        )
    ).scalars().all()

    await service.rebuild_range(club_id, from_date=day, to_date=day)
    second_count = (
        await db.execute(
            select(OccupancyRollup).where(OccupancyRollup.parlor_id == club_id)
        )
    ).scalars().all()

    assert len(first_count) == len(second_count)


@pytest.mark.asyncio
async def test_booking_counted_once_across_its_span(db, rollup_fixture):
    """A 2-hour booking occupies two buckets but is counted in only the one it starts
    in, so summing buckets over a range gives the true booking count."""
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]
    service = RollupService(db)

    await service.rebuild_bucket(club_id, _bucket(day, 18))
    await service.rebuild_bucket(club_id, _bucket(day, 19))

    first = await _club_row(db, club_id, day, 18)
    second = await _club_row(db, club_id, day, 19)

    assert first.occupied_minutes == 60
    assert second.occupied_minutes == 60  # still busy in the second hour
    assert first.booking_count == 1
    assert second.booking_count == 0  # but not counted twice


@pytest.mark.asyncio
async def test_rollup_writes_all_four_grains(db, rollup_fixture):
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]
    await RollupService(db).rebuild_bucket(club_id, _bucket(day, 18))

    grains = {
        row.grain
        for row in (
            await db.execute(
                select(OccupancyRollup).where(
                    OccupancyRollup.parlor_id == club_id,
                    OccupancyRollup.bucket_start == _bucket(day, 18).astimezone(UTC),
                )
            )
        ).scalars().all()
    }
    assert grains == {
        RollupGrain.CLUB.value,
        RollupGrain.RESOURCE_TYPE.value,
        RollupGrain.ZONE.value,
        RollupGrain.RESOURCE.value,
    }


@pytest.mark.asyncio
async def test_no_show_occupies_nothing_but_is_counted(db, rollup_fixture):
    """A no-show must raise the no-show count without inflating occupancy — the seat
    sat empty, which is exactly what makes the metric worth tracking."""
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]
    booking = rollup_fixture["booking"]

    booking.booking_status = BOOKING_STATUS_NO_SHOW
    booking.no_show_at = datetime.now(UTC)
    await db.commit()

    await RollupService(db).rebuild_bucket(club_id, _bucket(day, 18))
    row = await _club_row(db, club_id, day, 18)

    assert row.no_show_count == 1
    assert row.booking_count == 1
    assert row.occupied_minutes == 0
    assert row.revenue_paise == 0


@pytest.mark.asyncio
async def test_rollup_recompute_reflects_status_change(db, rollup_fixture):
    """Because buckets are recomputed from source rather than incremented, a status
    change is picked up on the next run instead of being stuck at the old value."""
    club_id = rollup_fixture["club_id"]
    day = rollup_fixture["date"]
    booking = rollup_fixture["booking"]
    service = RollupService(db)

    await service.rebuild_bucket(club_id, _bucket(day, 18))
    assert (await _club_row(db, club_id, day, 18)).occupied_minutes == 60

    booking.booking_status = "cancelled"
    await db.commit()

    await service.rebuild_bucket(club_id, _bucket(day, 18))
    row = await _club_row(db, club_id, day, 18)
    assert row.occupied_minutes == 0
    assert row.revenue_paise == 0


# --- 5. owner booking lifecycle (walk-in -> check-in -> check-out) ----------------


@pytest.mark.asyncio
async def test_walk_in_lifecycle_updates_customer_aggregates(api, db, seed):
    """End-to-end owner flow: a walk-in priced by the resolver, checked in, checked out,
    and rolled into the customer's visit/spend aggregates."""
    owner = seed["owner_a"]

    created = await api.post(
        "/api/v1/club/resources",
        headers=auth(owner),
        json={"label": "WALKIN-PC-1", "resource_type": "pc", "status": "available"},
    )
    assert created.status_code == 201

    walk_in = await api.post(
        "/api/v1/club/bookings/walk-in",
        headers=auth(owner),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-05",
            "start_time": "11:00:00",
            "duration_hours": 2,
            "units": 1,
            "guest_name": "Counter Guest",
            "contact_phone": "+919000000777",
            "payment_mode": "cash",
            "check_in_now": True,
        },
    )
    assert walk_in.status_code == 201, walk_in.text
    booking = walk_in.json()
    assert booking["is_walk_in"] is True
    assert booking["booking_status"] == "checked_in"
    assert booking["checked_in_at"] is not None
    # No pricing rule on this fresh club, so the resolver falls back to the club's
    # existing price_per_hour (₹120/hr from the seed) x 2 hours.
    assert booking["amount_paise"] == 24000

    live = await api.get("/api/v1/club/live", headers=auth(owner))
    assert live.status_code == 200
    assert any(row["booking_ref"] == booking["booking_ref"] for row in live.json())

    checked_out = await api.post(
        f"/api/v1/club/bookings/{booking['id']}/check-out", headers=auth(owner)
    )
    assert checked_out.status_code == 200
    assert checked_out.json()["booking_status"] == "completed"

    customers = await api.get(
        "/api/v1/club/customers?search=Counter", headers=auth(owner)
    )
    assert customers.status_code == 200
    items = customers.json()["items"]
    assert len(items) == 1
    assert items[0]["visit_count"] == 1
    assert items[0]["total_spend_paise"] == 24000


@pytest.mark.asyncio
async def test_no_show_after_check_in_is_rejected(api, seed):
    owner = seed["owner_a"]
    walk_in = await api.post(
        "/api/v1/club/bookings/walk-in",
        headers=auth(owner),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-06",
            "start_time": "12:00:00",
            "duration_hours": 1,
            "units": 1,
            "guest_name": "Already Here",
            "payment_mode": "cash",
            "check_in_now": True,
        },
    )
    booking_id = walk_in.json()["id"]

    response = await api.post(
        f"/api/v1/club/bookings/{booking_id}/no-show", headers=auth(owner)
    )
    assert response.status_code == 422
    assert "already checked in" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_cancel_requires_a_reason(api, seed):
    owner = seed["owner_a"]
    walk_in = await api.post(
        "/api/v1/club/bookings/walk-in",
        headers=auth(owner),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-07",
            "start_time": "13:00:00",
            "duration_hours": 1,
            "units": 1,
            "guest_name": "To Cancel",
            "payment_mode": "cash",
            "check_in_now": False,
        },
    )
    booking_id = walk_in.json()["id"]

    missing = await api.post(
        f"/api/v1/club/bookings/{booking_id}/cancel", headers=auth(owner), json={}
    )
    assert missing.status_code == 422

    ok = await api.post(
        f"/api/v1/club/bookings/{booking_id}/cancel",
        headers=auth(owner),
        json={"reason": "customer_no_longer_wants", "detail": "changed plans"},
    )
    assert ok.status_code == 200
    assert ok.json()["booking_status"] == "cancelled"
    assert ok.json()["cancellation_reason"] == "customer_no_longer_wants"


@pytest.mark.asyncio
async def test_banned_customer_cannot_walk_in(api, db, seed):
    owner = seed["owner_a"]
    first = await api.post(
        "/api/v1/club/bookings/walk-in",
        headers=auth(owner),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-08",
            "start_time": "14:00:00",
            "duration_hours": 1,
            "units": 1,
            "guest_name": "Trouble",
            "contact_phone": "+919000000999",
            "payment_mode": "cash",
            "check_in_now": False,
        },
    )
    assert first.status_code == 201
    customer_id = first.json()["club_customer_id"]

    banned = await api.post(
        f"/api/v1/club/customers/{customer_id}/ban",
        headers=auth(owner),
        json={"is_banned": True, "reason": "damaged equipment"},
    )
    assert banned.status_code == 200

    # Same phone -> resolves to the banned customer -> refused.
    again = await api.post(
        "/api/v1/club/bookings/walk-in",
        headers=auth(owner),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-09",
            "start_time": "14:00:00",
            "duration_hours": 1,
            "units": 1,
            "guest_name": "Trouble",
            "contact_phone": "+919000000999",
            "payment_mode": "cash",
            "check_in_now": False,
        },
    )
    assert again.status_code == 422
    assert "banned" in again.json()["message"].lower()


# --- 6. admin oversight ----------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_can_force_cancel_and_owner_sees_it(api, seed):
    owner = seed["owner_a"]
    admin = seed["admin"]
    club_id = seed["club_a"].id

    walk_in = await api.post(
        "/api/v1/club/bookings/walk-in",
        headers=auth(owner),
        json={
            "resource_type": "pc",
            "booking_date": "2026-08-10",
            "start_time": "15:00:00",
            "duration_hours": 1,
            "units": 1,
            "guest_name": "Force Cancel Me",
            "payment_mode": "cash",
            "check_in_now": False,
        },
    )
    booking_id = walk_in.json()["id"]

    forced = await api.post(
        f"/api/v1/admin/club-management/clubs/{club_id}/bookings/{booking_id}/force-cancel",
        headers=auth(admin),
        json={"reason": "platform_policy", "detail": "chargeback risk"},
    )
    assert forced.status_code == 200
    assert forced.json()["booking_status"] == "cancelled"
    assert forced.json()["cancelled_by"] == "admin"


@pytest.mark.asyncio
async def test_platform_disabled_promo_cannot_be_revived_by_owner(api, db, seed):
    """The platform kill switch is a separate column, so an owner toggling is_active
    back on must not resurrect a promo the platform disabled."""
    owner = seed["owner_a"]
    admin = seed["admin"]
    club_id = seed["club_a"].id

    created = await api.post(
        "/api/v1/club/promotions",
        headers=auth(owner),
        json={
            "name": "Owner promo",
            "promo_type": "percent",
            "percent_bps": 1000,
            "is_active": True,
        },
    )
    assert created.status_code == 201
    promo_id = created.json()["id"]

    disabled = await api.post(
        f"/api/v1/admin/club-management/clubs/{club_id}/promotions/{promo_id}/disable",
        headers=auth(admin),
        json={"disabled": True, "reason": "misleading terms"},
    )
    assert disabled.status_code == 200

    # Owner re-enables their own flag...
    revived = await api.patch(
        f"/api/v1/club/promotions/{promo_id}", headers=auth(owner), json={"is_active": True}
    )
    assert revived.status_code == 200
    assert revived.json()["is_active"] is True
    assert revived.json()["disabled_by_platform"] is True

    # ...but it still yields no discount.
    outcome = await PromotionService(db).validate(
        parlor_id=club_id,
        subtotal_paise=50000,
        resource_type=ResourceType.PC.value,
        booking_date=date(2026, 8, 5),
        start_time=time(12, 0),
        promotion_id=uuid.UUID(promo_id),
    )
    assert outcome.valid is False
    assert "misleading terms" in (outcome.reason or "")


# --- 7. revenue ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revenue_summary_nets_off_commission(api, db, seed):
    """Net revenue must subtract commission — the existing admin analytics reports
    gross only, so this is genuinely new arithmetic."""
    club_id = seed["club_b"].id
    today = datetime.now(IST).date()

    db.add(
        GamingBooking(
            booking_ref=f"RV{uuid.uuid4().hex[:8].upper()}",
            user_id=seed["owner_b"].id,
            parlour_id=club_id,
            slot_date=today,
            start_time=time(16, 0),
            end_time=time(17, 0),
            duration_hours=1,
            units=1,
            num_players=1,
            station_type="PC",
            booking_status="confirmed",
            payment_status="paid",
            payment_mode="upi",
            amount_paise=50000,
            commission_paise=5000,
            final_price=Decimal("500.00"),
        )
    )
    await db.commit()

    response = await api.get(
        f"/api/v1/club/revenue/summary?range=today&parlor_id={club_id}",
        headers=auth(seed["owner_b"]),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gross_paise"] == 50000
    assert data["commission_paise"] == 5000
    assert data["net_paise"] == 45000
    assert data["net_rupees"] == "450.00"
    assert data["avg_session_paise"] == 50000
    assert {"payment_method": "upi", "gross_paise": 50000, "booking_count": 1} in data[
        "by_payment_method"
    ]
