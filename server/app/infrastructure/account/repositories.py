"""
infrastructure/account/repositories.py

Репозиторий аккаунтов.
При загрузке аккаунта сразу достаёт разрешения одним запросом.
"""

from __future__ import annotations

from domain.entities.account import Account as DomainAccount
from domain.utils import generate_uuid
from sqlalchemy import exists, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.account.mapper import AccountMapper
from infrastructure.db.models.account import Account as ORMAccount
from infrastructure.db.models.permission import (
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
        permissions = await self._load_permissions(account_id)
        role_name = await self._load_role_name(account_id)
        return self._mapper.to_domain(account, permissions=permissions, role_name=role_name)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.email == email))
        account: ORMAccount | None = result.scalar_one_or_none()
        if account is None:
            return None
        permissions = await self._load_permissions(account.id)
        role_name = await self._load_role_name(account.id)
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

        await self._assign_default_role(orm.id)

        return self._mapper.to_domain(orm, permissions=frozenset(), role_name="user")

    async def _update(self, account: DomainAccount) -> DomainAccount:
        data = self._mapper.to_persistence(account)
        stmt = update(ORMAccount).where(ORMAccount.id == account.id).values(**data).returning(ORMAccount)
        result: Result = await self._session.execute(stmt)
        orm: ORMAccount = result.scalar_one()
        permissions = await self._load_permissions(orm.id)
        role_name = await self._load_role_name(orm.id)
        return self._mapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def _load_permissions(self, account_id: str) -> frozenset[str]:
        """Один JOIN-запрос для всех разрешений аккаунта."""
        result = await self._session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return frozenset(result.scalars().all())

    async def _load_role_name(self, account_id: str) -> str:
        result = await self._session.execute(
            select(Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return result.scalar_one_or_none() or "user"

    async def _assign_default_role(self, account_id: str) -> None:
        role_result = await self._session.execute(select(Role).where(Role.name == "user"))
        role = role_result.scalar_one_or_none()
        if not role:
            return  # роли ещё нет — lifespan инициализирует их

        stmt = (
            pg_insert(AccountRole)
            .values(id=generate_uuid(), account_id=account_id, role_id=role.id)
            .on_conflict_do_nothing(index_elements=["account_id"])
        )
        await self._session.execute(stmt)
