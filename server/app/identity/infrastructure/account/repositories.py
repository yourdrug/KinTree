"""
identity/infrastructure/account/repositories.py
"""

from __future__ import annotations

from typing import Any

from shared.domain.exceptions import NotFoundError
from shared.domain.permissions.enums import RoleName
from sqlalchemy import exists, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
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
        account = await self._fetch_with_role(ORMAccount.id == account_id)

        if account is None:
            raise NotFoundError(resource="Account", resource_id=account_id)
        return account

    async def get_by_email(self, email: str) -> DomainAccount | None:
        return await self._fetch_with_role(ORMAccount.email == email)

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

    # ── Private ───────────────────────────────────────────────────────────────

    async def _fetch_with_role(self, where_clause: Any) -> DomainAccount | None:
        """
        Один SELECT: account + role_id + role_name через LEFT JOIN.

        Путь при попадании в кэш (типичный): 1 запрос.
        Путь при промахе кэша: 2 запроса (+ array_agg permissions).

        array_agg не включаем в основной запрос намеренно:
        после прогрева кэша агрегация никогда не нужна, а JOIN с group_by
        усложняет план запроса и замедляет выборку account-полей.
        """
        stmt = (
            select(ORMAccount, Role.id.label("role_id"), Role.name.label("role_name"))
            .outerjoin(AccountRole, AccountRole.account_id == ORMAccount.id)
            .outerjoin(Role, Role.id == AccountRole.role_id)
            .where(where_clause)
        )
        result: Result = await self._session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        orm, role_id, role_name = row
        if role_name is None:
            role_name = RoleName.USER.value

        cached = get_cached_permissions(role_name)
        if cached is not None:
            return AccountMapper.to_domain(orm, permissions=cached, role_name=role_name)

        permissions = await self._fetch_permissions_for_role(role_id) if role_id else frozenset()
        set_cached_permissions(role_name, permissions)
        return AccountMapper.to_domain(orm, permissions=permissions, role_name=role_name)

    async def _load_role_and_permissions(self, account_id: str) -> tuple[str, frozenset[str]]:
        """Только для save(): account уже сохранён, нужно загрузить роль."""
        result = await self._session.execute(
            select(Role.id, Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        row = result.one_or_none()

        if row is None:
            return RoleName.USER.value, frozenset()

        role_id, role_name = row

        cached = get_cached_permissions(role_name)
        if cached is not None:
            return role_name, cached

        permissions = await self._fetch_permissions_for_role(role_id)
        set_cached_permissions(role_name, permissions)
        return role_name, permissions

    async def _fetch_permissions_for_role(self, role_id: str) -> frozenset[str]:
        """
        Все codenames для роли одним SELECT через array_agg.
        Возвращает одну строку вместо N строк — меньше data transfer.
        """
        result = await self._session.execute(
            select(func.array_agg(Permission.codename))
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        raw = result.scalar()
        return frozenset(raw) if raw else frozenset()
