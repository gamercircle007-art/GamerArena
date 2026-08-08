"""Partner onboarding: stations, hours, closures (admin/owner)."""

from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.gaming_booking.availability_service import AvailabilityService
from app.domains.gaming_booking.inventory_models import (
    ParlorClosure,
    ParlorHours,
    ParlorStation,
)
from app.domains.user.models import UserRole
from sqlalchemy import delete, select  # noqa: F401

router = APIRouter(prefix="/owner", tags=["Partner Onboarding"])


def _require_owner_or_admin(user) -> None:
    role = getattr(user, "role", None)
    val = role.value if hasattr(role, "value") else str(role)
    if val not in (UserRole.ADMIN.value, UserRole.PARLOR_OWNER.value, "admin", "parlor_owner"):
        raise HTTPException(status_code=403, detail="Owner or admin only")


class StationIn(BaseModel):
    station_type: str = Field(..., max_length=20)
    total_count: int = Field(..., ge=1, le=100)
    hourly_price_rupees: float = Field(..., ge=30)
    specs: dict | None = None


class HoursIn(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    open_time: time
    close_time: time


class ClosureIn(BaseModel):
    date: date
    reason: str | None = None


class OnboardStationsRequest(BaseModel):
    parlor_id: UUID
    stations: list[StationIn]


class OnboardHoursRequest(BaseModel):
    parlor_id: UUID
    hours: list[HoursIn]


@router.put("/parlors/{parlor_id}/stations")
async def upsert_stations(
    parlor_id: UUID,
    body: list[StationIn],
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    _require_owner_or_admin(current_user)
    await db.execute(delete(ParlorStation).where(ParlorStation.parlor_id == parlor_id))
    for s in body:
        db.add(
            ParlorStation(
                parlor_id=parlor_id,
                station_type=s.station_type.upper(),
                total_count=s.total_count,
                hourly_price_paise=int(round(s.hourly_price_rupees * 100)),
                is_active=True,
                specs=s.specs,
            )
        )
    await db.commit()
    return {"parlor_id": str(parlor_id), "stations": len(body)}


@router.put("/parlors/{parlor_id}/hours")
async def upsert_hours(
    parlor_id: UUID,
    body: list[HoursIn],
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    _require_owner_or_admin(current_user)
    await db.execute(delete(ParlorHours).where(ParlorHours.parlor_id == parlor_id))
    for h in body:
        db.add(
            ParlorHours(
                parlor_id=parlor_id,
                weekday=h.weekday,
                open_time=h.open_time,
                close_time=h.close_time,
            )
        )
    await db.commit()
    return {"parlor_id": str(parlor_id), "hours": len(body)}


@router.put("/parlors/{parlor_id}/closures")
async def upsert_closures(
    parlor_id: UUID,
    body: list[ClosureIn],
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    _require_owner_or_admin(current_user)
    await db.execute(delete(ParlorClosure).where(ParlorClosure.parlor_id == parlor_id))
    for c in body:
        db.add(ParlorClosure(parlor_id=parlor_id, date=c.date, reason=c.reason))
    await db.commit()
    return {"parlor_id": str(parlor_id), "closures": len(body)}


@router.get("/parlors/{parlor_id}/preview")
async def preview_slots(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
    date: date | None = None,
    station_type: str = "PC",
) -> dict:
    """Live preview of tomorrow's (or given date) availability for onboarding wizard."""
    _require_owner_or_admin(current_user)
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    d = date or (datetime_now_ist() + timedelta(days=1))
    slots = await AvailabilityService(db).compute_availability(parlor_id, d, station_type.upper())
    return {"parlor_id": str(parlor_id), "date": d.isoformat(), "station_type": station_type, "slots": slots}


def datetime_now_ist():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


@router.get("/parlors/{parlor_id}/config")
async def get_config(parlor_id: UUID, db: DbSessionDep, current_user: CurrentUserDep) -> dict:
    _require_owner_or_admin(current_user)
    stations = (
        await db.execute(select(ParlorStation).where(ParlorStation.parlor_id == parlor_id))
    ).scalars().all()
    hours = (
        await db.execute(select(ParlorHours).where(ParlorHours.parlor_id == parlor_id))
    ).scalars().all()
    closures = (
        await db.execute(select(ParlorClosure).where(ParlorClosure.parlor_id == parlor_id))
    ).scalars().all()
    return {
        "stations": [
            {
                "station_type": s.station_type,
                "total_count": s.total_count,
                "hourly_price_paise": s.hourly_price_paise,
            }
            for s in stations
        ],
        "hours": [
            {
                "weekday": h.weekday,
                "open_time": h.open_time.isoformat(),
                "close_time": h.close_time.isoformat(),
            }
            for h in hours
        ],
        "closures": [
            {"date": c.date.isoformat(), "reason": c.reason} for c in closures
        ],
    }
