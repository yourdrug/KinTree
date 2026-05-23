"""
identity/application/uow.py

Unit of Work — управление транзакцией.
"""

from __future__ import annotations

from contextlib import suppress
from types import TracebackType

from shared.domain.exceptions import DatabaseError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.repositories.account import AccountRepository
from identity.domain.repositories.email_token import EmailTokenRepository
from identity.domain.repositories.oauth_account import OAuthAccountRepository
from identity.domain.repositories.permission import (
    AccountRoleRepository,
    PermissionRepository,
    RoleRepository,
)
from identity.domain.repositories.refresh_tokens import RefreshTokenRepository


class IdentityUoW:
    accounts: AccountRepository
    permissions: PermissionRepository
    roles: RoleRepository
    account_roles: AccountRoleRepository
    refresh_tokens: RefreshTokenRepository
    oauth_accounts: OAuthAccountRepository
    email_tokens: EmailTokenRepository

    def __init__(
        self,
        session: AsyncSession,
        accounts: AccountRepository,
        permissions: PermissionRepository,
        roles: RoleRepository,
        account_roles: AccountRoleRepository,
        refresh_tokens: RefreshTokenRepository,
        oauth_accounts: OAuthAccountRepository,
        email_tokens: EmailTokenRepository,
    ) -> None:
        self._session = session
        self.accounts = accounts
        self.permissions = permissions
        self.roles = roles
        self.account_roles = account_roles
        self.refresh_tokens = refresh_tokens
        self.oauth_accounts = oauth_accounts
        self.email_tokens = email_tokens

    async def __aenter__(self) -> IdentityUoW:
        # Не вызываем session.begin() — SQLAlchemy 2.x autobegin включён по умолчанию.
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                with suppress(Exception):
                    await self._session.rollback()
        except DBAPIError as e:
            with suppress(Exception):
                await self._session.rollback()
            raise DatabaseError(detail=str(e)) from e
        finally:
            with suppress(Exception):
                await self._session.close()
