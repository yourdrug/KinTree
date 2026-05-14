"""
identity/infrastructure/account/repositories.py

Итоговая версия с обоими улучшениями:
1. save() — upsert, без двойного exists() SELECT
2. _load_role_and_permissions() — использует role_cache для permissions.
   Первый запрос роли → SELECT в БД + запись в кэш.
   Все последующие запросы той же роли → из кэша, 0 SELECT к permissions.
"""

from __future__ import annotations

from shared.domain.exceptions import NotFoundError
from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession

from identity.domain.entities.account import Account as DomainAccount
from identity.domain.entities.permission import get_default_role_name
from identity.infrastructure.account.mapper import AccountMapper
from identity.infrastructure.db.models.account import Account as ORMAccount
from identity.infrastructure.db.models.permission import (
    AccountRole,
    Permission,
    Role,
    RolePermission,
)
from identity.infrastructure.permissions.role_cache import (
    get_cached_permissions,
    set_cached_permissions,
)


class AccountRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, account_id: str) -> bool:
        stmt = select(exists().where(ORMAccount.id == account_id))
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def get_by_id(self, account_id: str) -> DomainAccount:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.id == account_id))
        orm: ORMAccount | None = result.scalar_one_or_none()

        if orm is None:
            raise NotFoundError(resource="Account", resource_id=account_id)

        role_name, permissions = await self._load_role_and_permissions(account_id)
        return AccountMapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def get_by_email(self, email: str) -> DomainAccount | None:
        result: Result = await self._session.execute(select(ORMAccount).where(ORMAccount.email == email))
        orm: ORMAccount | None = result.scalar_one_or_none()

        if orm is None:
            return None

        role_name, permissions = await self._load_role_and_permissions(orm.id)
        return AccountMapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def save(self, account: DomainAccount) -> DomainAccount:
        data = AccountMapper.to_persistence(account)
        stmt = (
            pg_insert(ORMAccount)
            .values(**data)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={k: v for k, v in data.items() if k != "id"},
            )
            .returning(ORMAccount)
        )
        result: Result = await self._session.execute(stmt)
        orm: ORMAccount = result.scalar_one()

        role_name, permissions = await self._load_role_and_permissions(orm.id)
        return AccountMapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def _load_role_and_permissions(self, account_id: str) -> tuple[str, frozenset[str]]:
        """
        Загружает роль аккаунта (1 SELECT всегда).
        Permissions — из глобального in-process кэша или из БД (1 SELECT при промахе).

        Типичный сценарий после прогрева:
          - 1 SELECT (роль аккаунта)
          - 0 SELECT (permissions из кэша)
        """
        role_result = await self._session.execute(
            select(Role.id, Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        row = role_result.one_or_none()

        if row is None:
            return get_default_role_name().value, frozenset()

        role_id, role_name = row

        cached = get_cached_permissions(role_name)

        if cached is not None:
            return role_name, cached

        # Если нет в кэше: загружаем из БД и кэшируем
        perm_result = await self._session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        permissions = frozenset(perm_result.scalars().all())
        set_cached_permissions(role_name, permissions)

        return role_name, permissions
