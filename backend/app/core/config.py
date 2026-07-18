"""
Application configuration using pydantic-settings.

All secrets and credentials are loaded from environment variables — never hardcoded.
Supports multiple environments via APP_ENV or ENVIRONMENT.

EXTENDING AUTH:
  - Set AUTH_METHODS to enable future providers (google, apple, email_otp, sms_otp)
  - Configure provider-specific sections below (OAuth, Email, SMS)
  - Implement provider in domains/auth/providers/ and register in providers/__init__.py
"""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "staging", "prod"]


class Settings(BaseSettings):
    """Central configuration for the Paythan backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_env: Environment = Field(
        default="local",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
        description="Deployment environment: local | dev | staging | prod",
    )
    app_name: str = "paythan"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # -------------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://paythan:changeme@localhost:5432/paythan",
        description="Async SQLAlchemy URL (postgresql+asyncpg://...)",
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Accept Render/Heroku-style URLs and force asyncpg + SSL for remote hosts.

        Render injects `postgresql://...` (or `postgres://...`). SQLAlchemy async
        needs `postgresql+asyncpg://`. Managed Postgres requires TLS.
        """
        if not isinstance(value, str) or not value:
            return value

        url = value.strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]

        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]

        is_local = any(
            host in url
            for host in (
                "@localhost",
                "@127.0.0.1",
                "@postgres:",  # docker-compose service name
                "@postgres/",
            )
        )
        if not is_local and "ssl=" not in url and "sslmode=" not in url:
            sep = "&" if "?" in url else "?"
            # asyncpg accepts ssl=require via query string
            url = f"{url}{sep}ssl=require"

        return url

    # External gaming-place catalog (projectX PostgreSQL) — synced on dev startup.
    gaming_places_database_url: str = Field(
        default="postgresql://projectx:projectx@localhost:5432/projectx",
        description="Source DB URL for gaming_places sync (postgresql://...)",
    )
    gaming_places_media_base_url: str = Field(
        default="http://localhost:8001",
        description="Base URL for relative /media/photos paths from gaming_places",
    )

    # -------------------------------------------------------------------------
    # Redis — OTP sessions, refresh token registry, login lockout
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------------
    # JWT
    # -------------------------------------------------------------------------
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # -------------------------------------------------------------------------
    # Authentication methods (comma-separated, extensible)
    # Current: whatsapp_otp, password
    # Future:   google, apple, email_otp, sms_otp
    # -------------------------------------------------------------------------
    auth_methods: str = "whatsapp_otp,password"

    # -------------------------------------------------------------------------
    # OTP — WhatsApp signup (default channel)
    # -------------------------------------------------------------------------
    otp_provider: str = "twilio"
    otp_expire_minutes: int = 10
    otp_length: int = 6
    otp_max_attempts: int = 5
    otp_rate_limit_count: int = 5
    otp_rate_limit_window_minutes: int = 10
    # Fixed OTP for local/dev only — leave empty in production
    otp_dev_bypass_code: str = ""

    # -------------------------------------------------------------------------
    # Twilio — WhatsApp OTP (primary) + SMS OTP fallback (future)
    # -------------------------------------------------------------------------
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    twilio_sms_from: str = ""

    # -------------------------------------------------------------------------
    # Email OTP — alternative channel (future)
    # Implement: domains/auth/providers/email_otp.py
    # -------------------------------------------------------------------------
    email_otp_enabled: bool = False
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_from_name: str = "Paythan"
    email_use_tls: bool = True

    # -------------------------------------------------------------------------
    # OAuth — Google / Apple Sign In (future)
    # Implement: domains/auth/providers/oauth/google.py
    # Add routes:  POST /auth/oauth/google, POST /auth/oauth/apple
    # -------------------------------------------------------------------------
    google_oauth_enabled: bool = False
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    apple_oauth_enabled: bool = False
    apple_client_id: str = ""
    apple_team_id: str = ""
    apple_key_id: str = ""
    apple_private_key_path: str = ""
    apple_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/apple/callback"

    # -------------------------------------------------------------------------
    # Login brute-force protection
    # -------------------------------------------------------------------------
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15

    # -------------------------------------------------------------------------
    # Argon2 password hashing
    # -------------------------------------------------------------------------
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    cors_allow_credentials: bool = True

    # -------------------------------------------------------------------------
    # AWS S3 / CloudFront — media uploads
    # -------------------------------------------------------------------------
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_cloudfront_domain: str = ""
    aws_region: str = "ap-south-1"

    # -------------------------------------------------------------------------
    # Razorpay — tournament entry fee payments
    # -------------------------------------------------------------------------
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    # -------------------------------------------------------------------------
    # Logging & security headers
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_json: bool = False
    allowed_hosts: str = "*"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        if self.allowed_hosts == "*":
            return ["*"]
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @property
    def auth_methods_list(self) -> list[str]:
        return [m.strip() for m in self.auth_methods.split(",") if m.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"

    @property
    def use_otp_dev_bypass(self) -> bool:
        """True when a fixed dev OTP is active (never in production)."""
        return bool(self.otp_dev_bypass_code) and not self.is_production

    @property
    def otp_rate_limit_window_seconds(self) -> int:
        return self.otp_rate_limit_window_minutes * 60

    def is_auth_method_enabled(self, method: str) -> bool:
        return method in self.auth_methods_list


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for FastAPI Depends()."""
    return Settings()