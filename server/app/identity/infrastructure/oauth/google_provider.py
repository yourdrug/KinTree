"""
identity/infrastructure/oauth/google_provider.py

Адаптер: Google Authorization Code flow → IOAuthProvider.
"""

from __future__ import annotations

from typing import Any

from identity.domain.ports.oauth_provider import OAuthUserInfo
from identity.infrastructure.oauth.google_verifier import get_google_user_info


class GoogleOAuthProvider:
    """Реализация IOAuthProvider для Google."""

    @property
    def provider_name(self) -> str:
        return "google"

    async def get_user_info(self, raw_data: dict[str, Any]) -> OAuthUserInfo:
        """
        raw_data ожидает: {"code": "<authorization_code>"}

        Raises:
            ValueError: если code невалиден или Google вернул ошибку.
        """
        code = raw_data.get("code")
        if not code:
            raise ValueError("Google OAuth: отсутствует authorization code")

        user_info = await get_google_user_info(code)

        return OAuthUserInfo(
            provider_user_id=user_info.sub,
            email=user_info.email,
            is_email_verified=user_info.email_verified,
            display_name=user_info.name,
            avatar_url=user_info.picture,
        )
