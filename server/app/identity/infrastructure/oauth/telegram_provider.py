"""
identity/infrastructure/oauth/telegram_provider.py
"""

from __future__ import annotations

from typing import Any

from identity.domain.ports.oauth_provider import OAuthUserInfo
from identity.domain.value_objects.email import Email
from identity.infrastructure.oauth.telegram_verifier import verify_telegram_auth


class TelegramOAuthProvider:
    @property
    def provider_name(self) -> str:
        return "telegram"

    async def get_user_info(self, raw_data: dict[str, Any]) -> OAuthUserInfo:
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

        # Email.create_synthetic — единственный способ создать синтетический email.
        # Домен "telegram.oauth" зарезервирован в Email VO, обычный create() его запретит.
        synthetic_email = Email.create_synthetic(f"tg_{user_info.telegram_id}@telegram.oauth")

        return OAuthUserInfo(
            provider_user_id=user_info.telegram_id,
            email=synthetic_email.value,
            is_email_verified=False,
            display_name=user_info.first_name,
            avatar_url=user_info.photo_url,
        )
