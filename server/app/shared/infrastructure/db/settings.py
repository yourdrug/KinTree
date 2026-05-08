"""
shared/infrastructure/db/settings.py

Все настройки приложения через pydantic-settings.
"""

from __future__ import annotations

from typing import ClassVar
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings: Class, containing settings for a project.
    """

    ENVIRONMENT: str
    BACKEND_CORS_ORIGINS: list[str]

    # Database — master
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # Database — slaves (опционально, для кластерного режима)
    DB_SLAVE_HOSTS: list[str] | None = Field(default=None)
    DB_SLAVE_PORTS: list[str] | None = Field(default=None)

    # Redis
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    JWT_TOKEN_ACCESS_LIFETIME_MINUTES: int = Field(default=10)
    JWT_TOKEN_REFRESH_LIFETIME_DAYS: int = Field(default=30)

    # Timezone (IANA tz name, например "Europe/Minsk", "UTC", "Europe/Moscow")
    TIMEZONE: str = Field(default="UTC")

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Telegram OAuth
    TELEGRAM_BOT_TOKEN: str

    RESEND_API_KEY: str
    EMAIL_FROM: str
    FRONTEND_URL: str

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore",
    )

    @field_validator("TIMEZONE")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except Exception as exception:
            raise ValueError(f"Invalid IANA timezone: {v!r}") from exception
        return v

    @property
    def tz(self) -> ZoneInfo:
        """Готовый объект ZoneInfo для использования в datetime.now(tz=settings.tz)."""
        return ZoneInfo(self.TIMEZONE)


settings: Settings = Settings()
