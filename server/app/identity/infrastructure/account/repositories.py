"""
identity/infrastructure/account/repositories.py

SQLAlchemy-реализация AccountRepository.
"""

from __future__ import annotations

from shared.domain.exceptions import NotFoundError
from sqlalchemy import exists, insert, select, update
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.entities.account import Account as DomainAccount
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
        """
        Возвращает аккаунт или бросает NotFoundError.
        Никогда не возвращает None — контракт репозитория.
        """
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.id == account_id))
        orm: ORMAccount | None = result.scalar_one_or_none()
        if orm is None:
            raise NotFoundError(resource="Account", resource_id=account_id)

        role_name, permissions = await self._load_role_and_permissions(account_id)
        return self._mapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.email == email))
        orm: ORMAccount | None = result.scalar_one_or_none()
        if orm is None:
            return None

        role_name, permissions = await self._load_role_and_permissions(orm.id)
        return self._mapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def save(self, account: DomainAccount) -> DomainAccount:
        """Upsert: INSERT если новый, UPDATE если существует."""
        if await self.exists(account.id):
            return await self._update(account)
        return await self._create(account)

    async def _create(self, account: DomainAccount) -> DomainAccount:
        data = self._mapper.to_persistence(account)
        stmt = insert(ORMAccount).values(**data).returning(ORMAccount)
        result: Result = await self._session.execute(stmt)
        orm: ORMAccount = result.scalar_one()
        # Новый аккаунт — роль ещё не назначена, возвращаем с пустыми правами.
        # AccountRole назначается отдельно после регистрации.
        return self._mapper.to_domain(orm, permissions=frozenset(), role_name="user")

    async def _update(self, account: DomainAccount) -> DomainAccount:
        data = self._mapper.to_persistence(account)
        stmt = update(ORMAccount).where(ORMAccount.id == account.id).values(**data).returning(ORMAccount)
        result: Result = await self._session.execute(stmt)
        orm: ORMAccount = result.scalar_one()
        role_name, permissions = await self._load_role_and_permissions(orm.id)
        return self._mapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def _load_role_and_permissions(self, account_id: str) -> tuple[str, frozenset[str]]:
        """
        Загружает роль и разрешения двумя запросами.
        Возвращает ("user", frozenset()) если роль не назначена.
        """
        role_result = await self._session.execute(
            select(Role.id, Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        row = role_result.one_or_none()
        if row is None:
            return "user", frozenset()

        role_id, role_name = row

        perm_result = await self._session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return role_name, frozenset(perm_result.scalars().all())
