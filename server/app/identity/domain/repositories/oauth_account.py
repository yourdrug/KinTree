"""
identity/domain/repositories/oauth_account.py

Порт репозитория OAuthAccount.
"""

from __future__ import annotations

from typing import Protocol

from identity.domain.entities.oauth_account import OAuthAccount, OAuthProvider


class OAuthAccountRepository(Protocol):
    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        """Найти привязку по провайдеру и ID пользователя у провайдера."""
        ...

    async def get_by_account_id(self, account_id: str) -> list[OAuthAccount]:
        """Все OAuth-привязки аккаунта."""
        ...

    async def create(self, oauth_account: OAuthAccount) -> None:
        """Сохранить новую привязку."""
        ...

    async def delete(self, oauth_account_id: str) -> None:
        """Удалить привязку."""
        ...
