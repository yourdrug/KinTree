from __future__ import annotations

from contextlib import suppress
from types import TracebackType

from shared.domain.exceptions import DatabaseError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.repositories.account import AccountRepository
from identity.domain.repositories.permission import (
    AccountRoleRepository,
    PermissionRepository,
    RoleRepository,
)


class IdentityUoW:
    """
    Unit of Work для Identity контекста.

    Содержит только то, что относится к Identity.
    Не знает о Genealogy.
    """

    accounts: AccountRepository
    permissions: PermissionRepository
    roles: RoleRepository
    account_roles: AccountRoleRepository

    def __init__(
        self,
        session: AsyncSession,
        accounts: AccountRepository,
        permissions: PermissionRepository,
        roles: RoleRepository,
        account_roles: AccountRoleRepository,
    ) -> None:
        self._session = session
        self.accounts = accounts
        self.permissions = permissions
        self.roles = roles
        self.account_roles = account_roles

    async def __aenter__(self) -> IdentityUoW:
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
