"""
identity/domain/repositories/email_token.py

Контракт репозитория EmailToken.
"""

from __future__ import annotations

from typing import Protocol

from identity.domain.entities.email_token import EmailToken, EmailTokenType


class EmailTokenRepository(Protocol):
    """Контракт хранилища EmailToken'ов."""

    async def create(self, token: EmailToken) -> EmailToken:
        """Сохранить новый токен."""
        ...

    async def get_valid_by_hash(
        self,
        token_hash: str,
        token_type: EmailTokenType,
    ) -> EmailToken | None:
        """
        Найти действующий токен по хэшу и типу.
        None если не найден, использован или истёк.
        """
        ...

    async def mark_used(self, token_id: str) -> None:
        """Пометить токен как использованный (одноразовость)."""
        ...

    async def invalidate_previous(
        self,
        account_id: str,
        token_type: EmailTokenType,
    ) -> None:
        """
        Аннулировать все предыдущие токены данного типа для аккаунта.
        Вызывается перед выдачей нового токена (resend / повторный запрос).
        """
        ...

    async def delete_expired(self) -> int:
        """Удалить истёкшие токены. Возвращает количество удалённых."""
        ...
