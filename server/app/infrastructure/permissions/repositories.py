"""
infrastructure/permissions/repositories.py

SQLAlchemy-реализации репозиториев системы разрешений.

Принципы:
- Реализует Protocol из domain/repositories/permission.py.
- Знает о ORM-моделях, не знает о доменной логике.
- upsert_many использует ON CONFLICT для идемпотентности.
- set_permissions — полная замена в рамках одной транзакции (UoW).
- Нет N+1: загрузка пермишенов для роли — один JOIN.
"""

from __future__ import annotations

from domain.entities.permission import AccountRole, Permission, Role
from sqlalchemy import Result, delete, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.permission import (
    AccountRole as AccountRoleORM,
)
from infrastructure.db.models.permission import (
    Permission as PermissionORM,
)
from infrastructure.db.models.permission import (
    Role as RoleORM,
)
from infrastructure.db.models.permission import (
    RolePermission as RolePermissionORM,
)
from infrastructure.permissions.mapper import AccountRoleMapper, PermissionMapper, RoleMapper


class PermissionRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Permission]:
        result: Result = await self._session.execute(select(PermissionORM))
        return [PermissionMapper.to_domain(p) for p in result.scalars().all()]

    async def get_by_codename(self, codename: str) -> Permission | None:
        result: Result = await self._session.execute(select(PermissionORM).where(PermissionORM.codename == codename))
        orm = result.scalar_one_or_none()
        return PermissionMapper.to_domain(orm) if orm else None

    async def get_by_codenames(self, codenames: list[str]) -> list[Permission]:
        if not codenames:
            return []
        result: Result = await self._session.execute(select(PermissionORM).where(PermissionORM.codename.in_(codenames)))
        return [PermissionMapper.to_domain(p) for p in result.scalars().all()]

    async def create(self, permission: Permission) -> Permission:
        data = PermissionMapper.to_persistence(permission)
        stmt = insert(PermissionORM).values(**data).returning(PermissionORM)
        result: Result = await self._session.execute(stmt)
        return PermissionMapper.to_domain(result.scalar_one())

    async def upsert_many(self, permissions: list[Permission]) -> list[Permission]:
        """
        Идемпотентный upsert по codename.
        Новые пермишены добавляются, существующие обновляют описание.
        """
        if not permissions:
            return []

        rows = [PermissionMapper.to_persistence(p) for p in permissions]

        stmt = (
            pg_insert(PermissionORM)
            .values(rows)
            .on_conflict_do_update(
                index_elements=["codename"],
                set_={"description": pg_insert(PermissionORM).excluded.description},
            )
            .returning(PermissionORM)
        )
        result: Result = await self._session.execute(stmt)
        return [PermissionMapper.to_domain(row) for row in result.scalars().all()]

    async def remove_all(self) -> None:
        await self._session.execute(delete(PermissionORM))


class RoleRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[Role]:
        result: Result = await self._session.execute(select(RoleORM))
        return [RoleMapper.to_domain(r) for r in result.scalars().all()]

    async def get_by_name(self, name: str) -> Role | None:
        result: Result = await self._session.execute(select(RoleORM).where(RoleORM.name == name))
        orm = result.scalar_one_or_none()
        return RoleMapper.to_domain(orm) if orm else None

    async def get_by_name_with_permissions(self, name: str) -> Role | None:
        """Роль + пермишены одним JOIN-запросом."""
        result: Result = await self._session.execute(select(RoleORM).where(RoleORM.name == name))
        orm_role = result.scalar_one_or_none()
        if not orm_role:
            return None

        perm_result: Result = await self._session.execute(
            select(PermissionORM)
            .join(RolePermissionORM, RolePermissionORM.permission_id == PermissionORM.id)
            .where(RolePermissionORM.role_id == orm_role.id)
        )
        permissions = [PermissionMapper.to_domain(p) for p in perm_result.scalars().all()]
        return RoleMapper.to_domain(orm_role, permissions)

    async def create(self, role: Role) -> Role:
        data = RoleMapper.to_persistence(role)
        stmt = insert(RoleORM).values(**data).returning(RoleORM)
        result: Result = await self._session.execute(stmt)
        return RoleMapper.to_domain(result.scalar_one())

    async def upsert_many(self, roles: list[Role]) -> list[Role]:
        """
        Идемпотентный upsert по name.
        Новые роли добавляются, существующие обновляют описание.
        """
        if not roles:
            return []

        rows = [RoleMapper.to_persistence(r) for r in roles]

        stmt = (
            pg_insert(RoleORM)
            .values(rows)
            .on_conflict_do_update(
                index_elements=["name"],
                set_={"description": pg_insert(RoleORM).excluded.description},
            )
            .returning(RoleORM)
        )
        result: Result = await self._session.execute(stmt)
        return [RoleMapper.to_domain(row) for row in result.scalars().all()]

    async def set_permissions(self, role_id: str, permission_ids: list[str]) -> None:
        """
        Полная замена набора пермишенов роли.
        DELETE старых + INSERT новых — атомарно через UoW.
        """
        # Удаляем все существующие связи для этой роли
        await self._session.execute(delete(RolePermissionORM).where(RolePermissionORM.role_id == role_id))

        if not permission_ids:
            return

        # Вставляем новые
        rows = [{"role_id": role_id, "permission_id": perm_id} for perm_id in permission_ids]
        await self._session.execute(insert(RolePermissionORM).values(rows))

    async def remove_all_role_permissions(self) -> None:
        await self._session.execute(delete(RolePermissionORM))

    async def remove_all(self) -> None:
        await self._session.execute(delete(RoleORM))


class AccountRoleRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_account_id(self, account_id: str) -> AccountRole | None:
        result: Result = await self._session.execute(
            select(AccountRoleORM).where(AccountRoleORM.account_id == account_id)
        )
        orm = result.scalar_one_or_none()
        return AccountRoleMapper.to_domain(orm) if orm else None

    async def assign_role(self, account_role: AccountRole) -> AccountRole:
        """
        Upsert: если у аккаунта уже есть роль — обновить,
        нет — создать. Идемпотентно.
        """
        data = AccountRoleMapper.to_persistence(account_role)

        stmt = (
            pg_insert(AccountRoleORM)
            .values(**data)
            .on_conflict_do_update(
                index_elements=["account_id"],
                set_={"role_id": pg_insert(AccountRoleORM).excluded.role_id},
            )
            .returning(AccountRoleORM)
        )
        result: Result = await self._session.execute(stmt)
        return AccountRoleMapper.to_domain(result.scalar_one())

    async def exists(self, account_id: str) -> bool:
        from sqlalchemy import exists as sql_exists
        from sqlalchemy import select

        stmt = select(sql_exists().where(AccountRoleORM.account_id == account_id))
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False
