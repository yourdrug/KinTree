"""
identy/application/account/service.py

Application-сервис для агрегата Account.
"""

from __future__ import annotations

from identity.domain.entities.account import Account
from identity.infrastructure.uow_factory import IdentityUoWFactory


class AccountService:
    """
    Application-сервис: управление агрегатом Account.

    Получает UoWFactory — фабрику Unit of Work.
    Каждый use case создаёт свой UoW (и транзакцию) через фабрику.
    """

    def __init__(self, uow_factory: IdentityUoWFactory) -> None:
        self._uow_factory = uow_factory

    async def get_account(self, account_id: str) -> Account:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.accounts.get_by_id(account_id)
