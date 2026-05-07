"""
identity/domain/entities/oauth_account.py

Агрегат OAuthAccount — привязка OAuth-провайдера к аккаунту.

Один аккаунт может иметь несколько OAuth-привязок (Google + Telegram).
Уникальность: (provider, provider_user_id) — один провайдер-аккаунт
не может быть привязан к двум разным аккаунтам.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.utils import generate_uuid

from identity.domain.entities.oauth_provider import OAuthProvider


@dataclass
class OAuthAccount:
    id: str
    account_id: str
    provider: OAuthProvider
    provider_user_id: str  # sub у Google, user.id у Telegram


def create_oauth_account(
    account_id: str,
    provider: OAuthProvider,
    provider_user_id: str,
) -> OAuthAccount:
    return OAuthAccount(
        id=generate_uuid(),
        account_id=account_id,
        provider=provider,
        provider_user_id=provider_user_id,
    )
