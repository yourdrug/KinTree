from __future__ import annotations

from typing import Protocol

from identity.domain.entities.account import Account


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

    async def exists(self, account_id: str) -> bool:
        """Проверить существование."""
        ...
