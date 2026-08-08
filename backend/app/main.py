"""
Paythan API entry point.

Routers are mounted per domain. Auth router handles signup, login, tokens.
See domains/auth/ for the full authentication module.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.chat.router import router as chat_router
from app.domains.common.exceptions import (
    AuthenticationError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.domains.booking.router import router as booking_router
from app.domains.friend.router import router as friend_router
from app.domains.messaging.router import router as messaging_router
from app.domains.online.router import router as online_router
from app.domains.snap_map.router import router as snap_map_router
from app.domains.story.router import router as story_router
from app.domains.payments.router import router as payments_router
from app.domains.comment.router import router as comment_router
from app.domains.feed.router import router as feed_router
from app.domains.feed.store_router import router as store_router
from app.domains.follow.router import router as follow_router
from app.routers.recommendation import router as recommendation_router
from app.domains.club_ops.admin_router import router as club_admin_router
from app.domains.club_ops.router import router as club_ops_router
from app.domains.gaming_booking.gc_points_router import router as gc_points_router
from app.domains.gaming_booking.parlor_router import router as gaming_parlor_router
from app.domains.gaming_booking.router import router as gaming_booking_router
from app.domains.gaming_booking.availability_router import router as availability_router
from app.domains.gaming_booking.onboarding_router import router as onboarding_router
from app.domains.geo.router import router as geo_router
from app.domains.home.router import router as home_router
from app.domains.like.router import router as like_router
from app.domains.notification.router import router as notification_router
from app.domains.parlor.router import router as parlor_router
from app.domains.post.router import router as post_router
from app.domains.reel.router import router as reel_router
from app.domains.search.router import router as search_router
from app.domains.tournament.router import router as tournament_router
from app.domains.dms.admin_router import router as admin_dms_router
from app.domains.dms.router import router as dms_router
from app.domains.upload.router import router as upload_router
from app.domains.user.router import router as user_router
from app.ws.router import router as ws_router

logger = get_logger(__name__)

OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": (
            "Enterprise auth: WhatsApp OTP signup, phone+password login, "
            "JWT access/refresh tokens with rotation. "
            "Future: Google OAuth, Apple Sign In, Email/SMS OTP."
        ),
    },
    {
        "name": "Users",
        "description": "User profile management for authenticated users.",
    },
    {
        "name": "Parlors",
        "description": "Gaming parlor profiles and tournament listings.",
    },
    {
        "name": "Tournaments",
        "description": "Tournament creation, discovery, and slot booking.",
    },
    {
        "name": "Bookings",
        "description": "Tournament slot booking with Redis locking and cancellation rules.",
    },
    {"name": "Posts", "description": "Parlor social posts and media."},
    {"name": "Reels", "description": "Short vertical video reels, likes, comments, and follows."},
    {"name": "Feed", "description": "Personalized feed from followed parlors."},
    {"name": "Comments", "description": "Threaded comments on posts."},
    {"name": "Likes", "description": "Like posts and comments."},
    {"name": "Follows", "description": "Follow gaming parlors."},
    {"name": "Home", "description": "OYO-style home feed, nearby parlors, and quick picks."},
    {
        "name": "Gaming Bookings",
        "description": "OYO-style gaming parlor slot booking, payment, and cancellation.",
    },
    {"name": "Gaming Parlors", "description": "OYO-style parlor search, detail, slots, and offers."},
    {"name": "GC Points", "description": "Loyalty points earned from gaming parlor bookings."},
    {"name": "Geo", "description": "Nearby parlors and tournaments via PostGIS."},
    {"name": "Search", "description": "Search parlors and tournaments."},
    {"name": "Notifications", "description": "In-app user notifications."},
    {"name": "Uploads", "description": "S3 presigned URL uploads (legacy — use DMS)."},
    {"name": "DMS", "description": "Centralized document/media management."},
    {"name": "Admin DMS", "description": "Admin media library and moderation."},
    {"name": "Payments", "description": "Razorpay tournament entry fees (Phase 3)."},
    {"name": "Tournament Chat", "description": "Tournament group chat via WebSocket."},
    {"name": "Messaging", "description": "Real-time conversations and direct messages."},
    {"name": "Friends", "description": "Friend requests, friendships, and blocks."},
    {"name": "Stories", "description": "24-hour expiring stories from friends."},
    {"name": "Snap Map", "description": "Friend locations on map with privacy controls."},
    {"name": "Profile", "description": "Extended user profiles and search."},
    {"name": "Online Status", "description": "Online presence and last seen."},
    {"name": "Admin", "description": "Admin panel API (Phase 3)."},
    {
        "name": "Health",
        "description": "Service health and readiness checks.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info("application_starting", app_name=settings.app_name, env=settings.app_env)

    readiness = settings.production_readiness()
    logger.info("production_readiness", **{k: str(v) for k, v in readiness.items()})
    if settings.is_production and not settings.twilio_configured:
        logger.error(
            "twilio_missing_in_production",
            hint="Set TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + TWILIO_WHATSAPP_FROM on Render",
        )
    if settings.is_production and settings.debug:
        logger.error("debug_enabled_in_production")

    import asyncio

    import redis.asyncio as aioredis

    from app.ws.manager import ws_manager

    # Keep Redis boot short: long retries delay /health and mark free-tier Failed.
    redis_client = aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        health_check_interval=30,
    )
    for attempt in range(1, 4):
        try:
            await redis_client.ping()
            logger.info("redis_ready", attempt=attempt)
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis_not_ready", attempt=attempt, error=str(exc))
            if attempt == 3:
                # Do not crash the whole API if Redis is briefly unavailable —
                # auth will 503; health still serves.
                logger.error("redis_unavailable_continuing_without_ws")
                try:
                    await redis_client.aclose()
                except Exception:  # noqa: BLE001
                    pass
                redis_client = None
                break
            await asyncio.sleep(1)

    if redis_client is not None:
        await ws_manager.start_redis_listener(redis_client)
    yield
    await ws_manager.stop()
    if redis_client is not None:
        await redis_client.aclose()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="GamerCircle API",
        description=(
            "## GamerCircle / GameConnect Backend\n\n"
            "Modular monolith: booking, social, messaging, reels, admin.\n\n"
            "### Authentication\n"
            "- **Signup**: Phone → WhatsApp OTP → Password → Account\n"
            "- **Login**: Phone + OTP or password → JWT tokens\n"
            "- **Security**: Argon2, Redis OTP, token rotation, rate limits\n"
        ),
        version="1.0.0",
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
        contact={"name": "GamerCircle Engineering"},
        license_info={"name": "Proprietary"},
    )

    # --- Security middleware ---
    if settings.allowed_hosts_list != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

    cors_kwargs: dict = {
        "allow_credentials": settings.cors_allow_credentials,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": ["X-Request-ID"],
    }
    origins = settings.cors_origins_list
    if settings.is_local:
        cors_kwargs["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
    elif origins == ["*"]:
        # Browsers forbid credentials + wildcard; native Flutter does not use CORS.
        cors_kwargs["allow_origins"] = ["*"]
        cors_kwargs["allow_credentials"] = False
    else:
        cors_kwargs["allow_origins"] = origins
    app.add_middleware(CORSMiddleware, **cors_kwargs)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # --- Exception handlers ---
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(exc, NotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, AuthenticationError):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, ForbiddenError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, RateLimitError):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        logger.warning("domain_error", code=exc.code, message=exc.message, path=request.url.path)
        return JSONResponse(
            status_code=status_code,
            content={"error": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        message = "Invalid request"
        if errors:
            first = errors[0]
            field = first.get("loc", ["field"])[-1]
            detail = first.get("msg", message)
            if field == "password":
                message = (
                    "Password must be at least 6 characters and include "
                    "uppercase, lowercase, and a number"
                )
            elif isinstance(field, str) and field != "body":
                message = f"{field}: {detail}"
            else:
                message = str(detail)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": message,
                "details": errors,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", path=request.url.path)
        # Surface error class in non-prod so Render/staging debugging is possible
        message = "An unexpected error occurred"
        if not settings.is_production:
            message = f"{type(exc).__name__}: {exc}"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "internal_error", "message": message},
        )

    @app.get("/health", tags=["Health"], summary="Health check (no I/O — always fast)")
    async def health_check() -> dict[str, Any]:
        """Liveness for Render. Must never touch DB/Redis or hang."""
        import os

        return {
            "status": "healthy",
            "service": settings.app_name,
            "environment": settings.app_env,
            "auth_methods": settings.auth_methods_list,
            "version": "1.0.0",
            "port": os.environ.get("PORT"),
            "twilio_configured": settings.twilio_configured,
            "otp_bypass_active": settings.use_otp_dev_bypass,
        }

    @app.get("/ready", tags=["Health"], summary="Readiness (DB + Redis + config)")
    async def readiness_check() -> dict[str, Any]:
        """Deeper check for ops / AI debugging. Never returns secrets."""
        import asyncio
        import os

        import redis.asyncio as aioredis
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        checks: dict[str, Any] = {"database": False, "redis": False}
        errors: dict[str, str] = {}

        async def check_db() -> None:
            try:
                engine = create_async_engine(settings.database_url, pool_pre_ping=True)
                async with engine.connect() as conn:
                    await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=5)
                checks["database"] = True
                await engine.dispose()
            except Exception as exc:  # noqa: BLE001
                errors["database"] = f"{type(exc).__name__}: {exc}"[:200]

        async def check_redis() -> None:
            try:
                client = aioredis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                await client.ping()
                checks["redis"] = True
                await client.aclose()
            except Exception as exc:  # noqa: BLE001
                errors["redis"] = f"{type(exc).__name__}: {exc}"[:200]

        await asyncio.gather(check_db(), check_redis())

        ready = checks["database"] and checks["redis"]
        body = {
            "status": "ready" if ready else "degraded",
            "checks": checks,
            "errors": errors,
            "config": settings.production_readiness(),
            "hints": _ready_hints(checks, settings),
            "git_sha": os.environ.get("RENDER_GIT_COMMIT")
            or os.environ.get("GIT_COMMIT")
            or "unknown",
        }
        if not ready:
            return JSONResponse(status_code=503, content=body)
        return body

    def _ready_hints(checks: dict[str, Any], s: Settings) -> list[str]:
        hints: list[str] = []
        if not checks.get("database"):
            hints.append(
                "E_DB: DATABASE_URL unreachable — link gamer-circle-db Internal URL"
            )
        if not checks.get("redis"):
            hints.append(
                "E_REDIS: REDIS_URL unreachable — OTP/sessions will fail; link Key Value"
            )
        if s.is_production and not s.twilio_configured:
            hints.append(
                "E_TWILIO: Set TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN + "
                "TWILIO_WHATSAPP_FROM for WhatsApp OTP"
            )
        if s.is_production and s.use_otp_dev_bypass:
            hints.append("E_OTP_BYPASS: OTP_DEV_BYPASS must be empty in prod")
        if not hints:
            hints.append("OK: DB + Redis up; OTP needs Twilio if not using password")
        return hints

    @app.post("/api/v1/dev/seed", tags=["Health"], summary="Bootstrap demo data (staging only)")
    async def dev_seed(request: Request) -> dict[str, Any]:
        """One-shot demo seed for empty Render DBs. Header: X-Seed-Key: OTP_DEV_BYPASS_CODE."""
        if settings.is_production:
            return JSONResponse(status_code=404, content={"error": "not_found"})
        key = request.headers.get("X-Seed-Key") or request.query_params.get("key")
        if not settings.otp_dev_bypass_code or key != settings.otp_dev_bypass_code:
            return JSONResponse(status_code=403, content={"error": "forbidden"})
        try:
            import importlib.util
            from pathlib import Path

            script = Path(__file__).resolve().parent.parent / "scripts" / "seed_render_bootstrap.py"
            spec = importlib.util.spec_from_file_location("seed_render_bootstrap", script)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Cannot load seed script: {script}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # Await async main() — never asyncio.run() inside the FastAPI loop
            await mod.main()
            return {
                "status": "ok",
                "message": "seed complete",
                "demo_login": "+919999999010 / Demo@123",
                "otp_bypass": settings.otp_dev_bypass_code,
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("dev_seed_failed")
            return JSONResponse(
                status_code=500,
                content={"error": "seed_failed", "message": str(exc)[:500]},
            )

    # --- Domain routers ---
    api_prefix = settings.api_v1_prefix
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(user_router, prefix=api_prefix)
    app.include_router(home_router, prefix=api_prefix)
    app.include_router(gaming_parlor_router, prefix=api_prefix)
    # availability before gaming_booking so /bookings/v2 is not captured as {booking_id}
    app.include_router(availability_router, prefix=api_prefix)
    app.include_router(gaming_booking_router, prefix=api_prefix)
    app.include_router(onboarding_router, prefix=api_prefix)
    app.include_router(gc_points_router, prefix=api_prefix)
    app.include_router(club_ops_router, prefix=api_prefix)
    app.include_router(club_admin_router, prefix=api_prefix)
    app.include_router(parlor_router, prefix=api_prefix)
    app.include_router(tournament_router, prefix=api_prefix)
    app.include_router(booking_router, prefix=api_prefix)
    app.include_router(post_router, prefix=api_prefix)
    app.include_router(reel_router, prefix=api_prefix)
    app.include_router(feed_router, prefix=api_prefix)
    app.include_router(store_router, prefix=api_prefix)
    app.include_router(comment_router, prefix=api_prefix)
    app.include_router(like_router, prefix=api_prefix)
    app.include_router(follow_router, prefix=api_prefix)
    app.include_router(geo_router, prefix=api_prefix)
    app.include_router(search_router, prefix=api_prefix)
    app.include_router(notification_router, prefix=api_prefix)
    app.include_router(dms_router, prefix=api_prefix)
    app.include_router(admin_dms_router, prefix=api_prefix)
    app.include_router(upload_router, prefix=api_prefix)
    app.include_router(payments_router, prefix=api_prefix)
    # Spec alias: POST /api/v1/webhooks/cashfree → same handler (mounted under payments too)
    app.include_router(chat_router, prefix=api_prefix)
    app.include_router(messaging_router, prefix=api_prefix)
    app.include_router(friend_router, prefix=api_prefix)
    app.include_router(story_router, prefix=api_prefix)
    app.include_router(snap_map_router, prefix=api_prefix)
    app.include_router(online_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)
    app.include_router(recommendation_router, prefix=api_prefix)
    app.include_router(ws_router)

    return app


app = create_app()