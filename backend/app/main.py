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

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.domains.admin.router import router as admin_router
from app.domains.auth.router import router as auth_router
from app.domains.chat.router import router as chat_router
from app.domains.common.exceptions import (
    AuthenticationError,
    DomainError,
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
from app.domains.gaming_booking.gc_points_router import router as gc_points_router
from app.domains.gaming_booking.parlor_router import router as gaming_parlor_router
from app.domains.gaming_booking.router import router as gaming_booking_router
from app.domains.geo.router import router as geo_router
from app.domains.home.router import router as home_router
from app.domains.like.router import router as like_router
from app.domains.notification.router import router as notification_router
from app.domains.parlor.router import router as parlor_router
from app.domains.post.router import router as post_router
from app.domains.reel.router import router as reel_router
from app.domains.search.router import router as search_router
from app.domains.tournament.router import router as tournament_router
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
    {"name": "Uploads", "description": "S3 presigned URL uploads."},
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

    import redis.asyncio as aioredis

    from app.ws.manager import ws_manager

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    await ws_manager.start_redis_listener(redis_client)
    yield
    await ws_manager.stop()
    await redis_client.aclose()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name.title()} API",
        description=(
            "## Paythan Backend API\n\n"
            "Modular monolith with domain-driven design.\n\n"
            "### Authentication\n"
            "- **Signup**: Name + Email + Phone → WhatsApp OTP → Password → Account\n"
            "- **Login**: Phone + Password → JWT tokens\n"
            "- **Security**: Argon2 passwords, Redis OTP, token rotation, brute-force lockout\n\n"
            "### Extensibility\n"
            "OAuth (Google/Apple) and alternative OTP channels (Email/SMS) are scaffolded "
            "in `domains/auth/providers/`."
        ),
        version="0.2.0",
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
        contact={"name": "Paythan Engineering"},
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
    if settings.is_local:
        cors_kwargs["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
    else:
        cors_kwargs["allow_origins"] = settings.cors_origins_list
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
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "internal_error", "message": "An unexpected error occurred"},
        )

    @app.get("/health", tags=["Health"], summary="Health check")
    async def health_check() -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": settings.app_name,
            "environment": settings.app_env,
            "auth_methods": settings.auth_methods_list,
        }

    # --- Domain routers ---
    api_prefix = settings.api_v1_prefix
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(user_router, prefix=api_prefix)
    app.include_router(home_router, prefix=api_prefix)
    app.include_router(gaming_parlor_router, prefix=api_prefix)
    app.include_router(gaming_booking_router, prefix=api_prefix)
    app.include_router(gc_points_router, prefix=api_prefix)
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
    app.include_router(upload_router, prefix=api_prefix)
    app.include_router(payments_router, prefix=api_prefix)
    app.include_router(chat_router, prefix=api_prefix)
    app.include_router(messaging_router, prefix=api_prefix)
    app.include_router(friend_router, prefix=api_prefix)
    app.include_router(story_router, prefix=api_prefix)
    app.include_router(snap_map_router, prefix=api_prefix)
    app.include_router(online_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)
    app.include_router(ws_router)

    return app


app = create_app()