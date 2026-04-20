from __future__ import annotations

from typing import Protocol

from domain.entities.account import Account


class AccountRepository(Protocol):
    async def get_by_id(self, account_id: str) -> Account:
        """Возвращает аккаунт или бросает NotFoundError."""
        ...

    async def get_by_email(self, email: str) -> Account | None:
        """Возвращает аккаунт по email или None."""
        ...

    async def save(self, account: Account) -> Account:
        """Создать или обновить. Возвращает сохранённый объект."""
        ...

    async def update_refresh_token(
        self,
        account_id: str,
        hashed_refresh_token: str | None,
    ) -> None:
        """Обновить хэш refresh-токена (или очистить при logout)."""
        ...

    async def exists(self, account_id: str) -> bool:
        """Проверить существование."""
        ...
