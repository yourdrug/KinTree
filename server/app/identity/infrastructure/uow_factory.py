from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from shared.infrastructure.db.database import DatabaseManager
from identity.application.uow import IdentityUoW
from identity.infrastructure.account.repositories import AccountRepositoryImpl
from identity.infrastructure.permissions.repositories import (
    AccountRoleRepositoryImpl,
    PermissionRepositoryImpl,
    RoleRepositoryImpl,
)


class IdentityUoWFactory:
    def __init__(self, database: DatabaseManager) -> None:
        self._database = database

    @asynccontextmanager
    async def create(
        self, master: bool = False
    ) -> AsyncGenerator[IdentityUoW, None]:
        session = self._database.get_session(master=master)
        uow = IdentityUoW(
            session=session,
            accounts=AccountRepositoryImpl(session=session),
            permissions=PermissionRepositoryImpl(session=session),
            roles=RoleRepositoryImpl(session=session),
            account_roles=AccountRoleRepositoryImpl(session=session),
        )

        async with uow:
            yield uow
