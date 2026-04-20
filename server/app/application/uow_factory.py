"""
application/uow_factory.py

Фабрика Unit of Work.

Принципы:
- Фабрика создаёт UoW с нужной сессией (master/slave) и инжектирует репозитории.
- Application-сервисы зависят от UoWFactory, а не от конкретной сессии БД.
- Репозитории создаются внутри фабрики — сервис не знает об ORM.
- Поддержка master/slave: master=True → пишущая сессия, master=False → читающая.

Пример использования:
    # В dependency injection (FastAPI):
    def get_person_service(db: DatabaseManager = Depends(get_database)):
        return PersonService(uow_factory=UoWFactory(db))

    # В сервисе:
    async with self._uow_factory.create(master=True) as uow:
        await uow.persons.save(person)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from infrastructure.account.repositories import AccountRepositoryImpl
from infrastructure.db.database import DatabaseManager
from infrastructure.family.repositories import FamilyRepositoryImpl
from infrastructure.permissions.repositories import (
    AccountRoleRepositoryImpl,
    PermissionRepositoryImpl,
    RoleRepositoryImpl,
)
from infrastructure.person.repositories import PersonRepositoryImpl
from infrastructure.relations.repositories import ParentChildRepositoryImpl, SpouseRepositoryImpl

from application.uow import UnitOfWork


class UoWFactory:
    """
    Создаёт UnitOfWork с нужной DB-сессией и репозиториями.

    Принимает DatabaseManager — знает о master/slave.
    Внедряется в application-сервисы через DI-контейнер.
    """

    def __init__(self, database: DatabaseManager) -> None:
        self._database = database

    @asynccontextmanager
    async def create(self, master: bool = False) -> AsyncGenerator[UnitOfWork, None]:
        """
        Создаёт UoW как async context manager.

        Использование:
            async with uow_factory.create(master=True) as uow:
                await uow.persons.save(person)
        """
        session = self._database.get_session(master=master)

        persons = PersonRepositoryImpl(session=session)
        families = FamilyRepositoryImpl(session=session)
        accounts = AccountRepositoryImpl(session=session)
        spouses = SpouseRepositoryImpl(session=session)
        parent_child = ParentChildRepositoryImpl(session=session)
        permissions = PermissionRepositoryImpl(session=session)
        roles = RoleRepositoryImpl(session=session)
        account_roles = AccountRoleRepositoryImpl(session=session)

        uow = UnitOfWork(
            session=session,
            persons=persons,
            families=families,
            accounts=accounts,
            parent_child=parent_child,
            spouses=spouses,
            permissions=permissions,
            roles=roles,
            account_roles=account_roles,
        )

        async with uow:
            yield uow
