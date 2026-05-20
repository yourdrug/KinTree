"""
identity/domain/ports/oauth_provider.py

Port: абстракция OAuth-провайдера.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class OAuthUserInfo:
    """
    Нормализованные данные пользователя от любого OAuth-провайдера.

    provider_user_id — уникальный ID у провайдера (sub у Google, id у Telegram).
    email — реальный email или None если провайдер не даёт (Telegram).
    is_email_verified — False для провайдеров без верификации email.
    display_name — опционально, для будущего профиля.
    """

    provider_user_id: str
    email: str | None
    is_email_verified: bool
    display_name: str | None = None
    avatar_url: str | None = None


class IOAuthProvider(Protocol):
    """
    Port: верификация и получение данных от OAuth-провайдера.

    Каждый провайдер реализует этот протокол.
    OAuthService работает только с IOAuthProvider, не знает о конкретных провайдерах.
    """

    @property
    def provider_name(self) -> str:
        """
        Имя провайдера — совпадает с OAuthProvider enum value.
        Пример: 'google', 'telegram', 'github'.
        """
        ...

    async def get_user_info(self, raw_data: dict[str, Any]) -> OAuthUserInfo:
        """
        Верифицировать данные и вернуть нормализованный OAuthUserInfo.

        raw_data — всё что пришло от провайдера:
          Google:   {"code": "4/0AfJ..."}
          Telegram: {"id": "123", "first_name": "...", "hash": "...", ...}
          GitHub:   {"code": "..."}

        Raises:
            ValueError: если данные невалидны (плохая подпись, истёкший код и т.д.)
        """
        ...
