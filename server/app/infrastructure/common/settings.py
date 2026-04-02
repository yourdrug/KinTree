from typing import (
    ClassVar, Optional,
)

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from pytz import timezone


TIMEZONE = timezone('Europe/Minsk')


class Settings(BaseSettings):
    """
    Settings: Class, containing settings for a project.
    """

    ENVIRONMENT: str
    BACKEND_CORS_ORIGINS: list[str]

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_SLAVE_HOSTS: Optional[list[str]] = Field(default=None)
    DB_SLAVE_PORTS: Optional[list[str]] = Field(default=None)

    SECRET_KEY: str
    JWT_TOKEN_ACCESS_LIFETIME_MINUTES: int = Field(default=15)
    JWT_TOKEN_REFRESH_LIFETIME_DAYS: int = Field(default=1)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        case_sensitive=True,
    )


settings: Settings = Settings()
