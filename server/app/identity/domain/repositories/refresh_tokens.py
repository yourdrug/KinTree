"""
identity/domain/repositories/refresh_tokens.py

Контракт репозитория RefreshToken.
"""

from __future__ import annotations

from typing import Protocol

from identity.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(Protocol):
    """Контракт хранилища RefreshToken'ов."""

    async def create(
        self,
        account_id: str,
        session_id: str,
        token_hash: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """Создать новый refresh token."""
        ...

    async def get_by_session_id(self, session_id: str) -> RefreshToken | None:
        """Найти по session_id. None если не существует."""
        ...

    async def get_active_by_account(self, account_id: str) -> list[RefreshToken]:
        """Все активные (не отозванные, не истёкшие) токены аккаунта."""
        ...

    async def revoke_by_session_id(self, session_id: str) -> None:
        """Отозвать одну сессию."""
        ...

    async def revoke_all_by_account(self, account_id: str) -> None:
        """Отозвать все сессии аккаунта (при детекте компрометации)."""
        ...

    async def delete_expired(self) -> int:
        """Удалить истёкшие токены. Возвращает количество удалённых."""
        ...
