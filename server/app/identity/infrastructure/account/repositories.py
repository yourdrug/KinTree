"""
infrastructure/account/repositories.py

Репозиторий аккаунтов.
При загрузке аккаунта сразу достаёт разрешения одним запросом.
"""

from __future__ import annotations

from identity.domain.entities.account import Account as DomainAccount
from sqlalchemy import exists, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.permissions.enums import RoleName
from identity.infrastructure.account.mapper import AccountMapper
from identity.infrastructure.db.models.account import Account as ORMAccount
from identity.infrastructure.db.models.permission import (
    AccountRole,
    Permission,
    Role,
    RolePermission,
)


class AccountRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mapper = AccountMapper()

    async def exists(self, account_id: str) -> bool:
        stmt = select(exists().where(ORMAccount.id == account_id))
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def get_by_id(self, account_id: str) -> DomainAccount:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.id == account_id))
        account: ORMAccount = result.scalar_one()
        role_name, permissions = await self._load_role_and_permissions(account_id)
        return self._mapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.email == email))
        account: ORMAccount | None = result.scalar_one_or_none()
        if account is None:
            return None
        role_name, permissions = await self._load_role_and_permissions(account.id)
        return self._mapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def save(self, account: DomainAccount) -> DomainAccount:
        """Upsert: INSERT если новый, UPDATE если существует."""
        if await self.exists(account.id):
            return await self._update(account)
        return await self._create(account)

    async def update_refresh_token(
        self,
        account_id: str,
        hashed_refresh_token: str | None,
    ) -> None:
        statement = update(ORMAccount).where(ORMAccount.id == account_id).values(refresh_token=hashed_refresh_token)
        await self._session.execute(statement)

    # ── Private helpers ────────────────────────────────────────────────────

    async def _create(self, account: DomainAccount) -> DomainAccount:
        data = self._mapper.to_persistence(account)
        stmt = insert(ORMAccount).values(**data).returning(ORMAccount)
        result: Result = await self._session.execute(stmt)
        orm: ORMAccount = result.scalar_one()
        return self._mapper.to_domain(orm, permissions=frozenset(), role_name=RoleName.USER.value)

    async def _update(self, account: DomainAccount) -> DomainAccount:
        data = self._mapper.to_persistence(account)
        stmt = update(ORMAccount).where(ORMAccount.id == account.id).values(**data).returning(ORMAccount)
        result: Result = await self._session.execute(stmt)
        orm: ORMAccount = result.scalar_one()
        role_name, permissions = await self._load_role_and_permissions(orm.id)
        return self._mapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def _load_role_and_permissions(self, account_id: str) -> tuple[str, frozenset[str]]:
        """One query: role name + all permission codenames."""

        # Step 1: get role
        role_result = await self._session.execute(
            select(Role.id, Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        row = role_result.one_or_none()
        if row is None:
            return "user", frozenset()

        role_id, role_name = row

        # Step 2: get permissions for that role_id
        perm_result = await self._session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return role_name, frozenset(perm_result.scalars().all())
