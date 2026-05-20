"""
identity/infrastructure/oauth/telegram_provider.py

Адаптер: Telegram Login Widget → IOAuthProvider.
"""

from __future__ import annotations

from typing import Any

from identity.domain.ports.oauth_provider import OAuthUserInfo
from identity.infrastructure.oauth.telegram_verifier import verify_telegram_auth


class TelegramOAuthProvider:
    """Реализация IOAuthProvider для Telegram Login Widget."""

    # Зарезервированный домен для синтетических email Telegram-аккаунтов.
    # Совпадает с _RESERVED_DOMAINS в Email value object.
    _SYNTHETIC_EMAIL_DOMAIN = "telegram.oauth"

    @property
    def provider_name(self) -> str:
        return "telegram"

    async def get_user_info(self, raw_data: dict[str, Any]) -> OAuthUserInfo:
        """
        raw_data ожидает поля от Telegram Login Widget:
          id, first_name, auth_date, hash, [last_name, username, photo_url]

        Raises:
            ValueError: если подпись невалидна или данные устарели.
        """
        try:
            user_info = verify_telegram_auth(
                telegram_id=str(raw_data["id"]),
                first_name=raw_data["first_name"],
                last_name=raw_data.get("last_name"),
                username=raw_data.get("username"),
                photo_url=raw_data.get("photo_url"),
                auth_date=int(raw_data["auth_date"]),
                received_hash=raw_data["hash"],
            )
        except KeyError as exc:
            raise ValueError(f"Telegram OAuth: отсутствует поле {exc}") from exc

        # Telegram не предоставляет email — используем синтетический идентификатор.
        # Домен зарезервирован в Email VO: обычный пользователь не может его зарегистрировать.
        synthetic_email = f"tg_{user_info.telegram_id}@{self._SYNTHETIC_EMAIL_DOMAIN}"

        return OAuthUserInfo(
            provider_user_id=user_info.telegram_id,
            email=synthetic_email,
            is_email_verified=False,  # синтетический email — верифицировать нечего
            display_name=user_info.first_name,
            avatar_url=user_info.photo_url,
        )
