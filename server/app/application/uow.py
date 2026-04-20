"""
application/uow.py

Unit of Work — единственный способ начать транзакцию в application-слое.

Принципы:
- UoW владеет всеми репозиториями.
- Репозитории НЕ управляют транзакциями сами.
- Application-сервис работает через UoW как контекстный менеджер.
- Нет наследования от BaseService — сервисы получают UoW через __init__.

Пример использования в сервисе:
    async with self.uow:
        person = await self.uow.persons.get_by_id(person_id)
        family = await self.uow.families.get_by_id(person.family_id)
        # ... бизнес-логика ...
        await self.uow.persons.save(person)
"""

from __future__ import annotations

from contextlib import suppress
from types import TracebackType

from domain.exceptions import DatabaseError
from domain.repositories.account import AccountRepository
from domain.repositories.family import FamilyRepository
from domain.repositories.person import PersonRepository
from domain.repositories.relations import ParentChildRepository, SpouseRepository
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """
    Единица работы — оборачивает транзакцию и предоставляет репозитории.

    Используется как асинхронный контекстный менеджер:

        async with uow:
            person = await uow.persons.get_by_id(person_id)
            await uow.persons.save(person)
            # commit произойдёт автоматически при выходе без исключения
    """

    persons: PersonRepository
    families: FamilyRepository
    accounts: AccountRepository
    parent_child: ParentChildRepository
    spouses: SpouseRepository

    def __init__(
        self,
        session: AsyncSession,
        persons: PersonRepository,
        families: FamilyRepository,
        accounts: AccountRepository,
        parent_child: ParentChildRepository,
        spouses: SpouseRepository,
    ) -> None:
        self._session = session
        self.persons = persons
        self.families = families
        self.accounts = accounts
        self.parent_child = parent_child
        self.spouses = spouses

    async def __aenter__(self) -> UnitOfWork:
        await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        with suppress(Exception):
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()

        with suppress(Exception):
            await self._session.close()

        if exc_type is not None and issubclass(exc_type, DBAPIError):
            raise DatabaseError(detail=str(exc_val)) from exc_val
