from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./admin.db"
    ADMIN_JWT_SECRET: str = "admin-dev-secret-change-in-production-32chars"
    ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ADMIN_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_DEV_BYPASS_CODE: str = "123456"
    ALLOWED_ORIGINS: str = (
        "http://localhost:4200,http://127.0.0.1:4200,"
        "http://localhost:3001,http://127.0.0.1:3001"
    )
    ENVIRONMENT: str = "development"
    PORT: int = 8001

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()