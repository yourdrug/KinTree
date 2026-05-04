from __future__ import annotations

from typing import Protocol

from identity.infrastructure.db.models.refresh_token import RefreshToken


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
        """Найти refresh token по session_id."""
        ...

    async def get_active_by_account(self, account_id: str) -> list[RefreshToken]:
        """Получить все активные токены аккаунта."""
        ...

    async def revoke_by_session_id(self, session_id: str) -> None:
        """Отозвать один refresh token."""
        ...

    async def revoke_all_by_account(self, account_id: str) -> None:
        """Отозвать все refresh token'ы аккаунта."""
        ...

    async def delete_expired(self) -> int:
        """Удалить все истёкшие токены."""
        ...
