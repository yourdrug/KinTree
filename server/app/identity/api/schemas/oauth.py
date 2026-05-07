"""
identity/api/schemas/oauth.py

Pydantic-схемы для OAuth эндпоинтов.
"""

from __future__ import annotations

from presentation.rest.dependencies.request_meta import RequestMeta
from pydantic import BaseModel, Field

from identity.application.oauth.commands import TelegramCallbackCommand


class TelegramCallbackRequest(BaseModel):
    """
    Данные от Telegram Login Widget.

    Telegram присылает их как GET-параметры в redirect URL,
    или POST-телом если используется JS callback.
    Принимаем как query params (см. роут).
    """

    id: str = Field(..., description="Telegram user ID")
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str

    def to_command(self, meta: RequestMeta) -> TelegramCallbackCommand:
        return TelegramCallbackCommand(
            telegram_id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            photo_url=self.photo_url,
            auth_date=self.auth_date,
            hash=self.hash,
            user_agent=meta.user_agent,
            ip_address=meta.ip_address,
        )
