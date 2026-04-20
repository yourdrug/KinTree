"""
infrastructure/permissions/repositories.py

Реализации репозиториев системы разрешений.

Ключевые решения:
- get_account_permissions использует один JOIN-запрос (не N+1)
- ensure_* методы идемпотентны (ON CONFLICT DO NOTHING)
- Все строковые операции идут через параметры, не f-строки
"""

from __future__ import annotations

from domain.entities.permission import AccountRoleEntity, PermissionEntity, RoleEntity, RolePermissionEntity
from sqlalchemy import Result, delete, exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.permission import (
    AccountRole as ORMAccountRole,
)
from infrastructure.db.models.permission import (
    Permission as ORMPermission,
)
from infrastructure.db.models.permission import (
    Role as ORMRole,
)
from infrastructure.db.models.permission import (
    RolePermission as ORMRolePermission,
)
from infrastructure.permissions.mapper import (
    AccountRoleMapper,
    PermissionMapper,
    RoleMapper,
    RolePermissionMapper,
)


class PermissionRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[PermissionEntity]:
        result: Result = await self._session.execute(select(ORMPermission))
        return [PermissionMapper.to_domain(p) for p in result.scalars().all()]

    async def get_by_codename(self, codename: str) -> PermissionEntity | None:
        stmt = select(ORMPermission).where(ORMPermission.codename == codename)
        result: Result = await self._session.execute(stmt)

        orm = result.scalar_one_or_none()
        return PermissionMapper.to_domain(orm) if orm else None

    async def create(self, permission: PermissionEntity) -> PermissionEntity:
        data = PermissionMapper.to_persistence(permission)

        stmt = insert(ORMPermission).values(**data).returning(ORMPermission)
        result: Result = await self._session.execute(stmt)

        return PermissionMapper.to_domain(result.scalar_one())

    async def remove_all(self) -> None:
        await self._session.execute(delete(ORMPermission))


class RoleRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[RoleEntity]:
        result: Result = await self._session.execute(select(ORMRole))
        return [RoleMapper.to_domain(r) for r in result.scalars().all()]

    async def get_by_name(self, name: str) -> RoleEntity | None:
        stmt = select(ORMRole).where(ORMRole.name == name)
        result: Result = await self._session.execute(stmt)

        orm = result.scalar_one_or_none()
        return RoleMapper.to_domain(orm) if orm else None

    async def get_with_permissions(self, name: str) -> RoleEntity | None:
        stmt = select(ORMRole).where(ORMRole.name == name)
        result: Result = await self._session.execute(stmt)

        orm_role = result.scalar_one_or_none()
        if not orm_role:
            return None

        perm_result = await self._session.execute(
            select(ORMPermission)
            .join(ORMRolePermission, ORMRolePermission.permission_id == ORMPermission.id)
            .where(ORMRolePermission.role_id == orm_role.id)
        )

        permissions = [PermissionMapper.to_domain(p) for p in perm_result.scalars().all()]
        return RoleMapper.to_domain(orm_role, permissions)

    async def create(self, role: RoleEntity) -> RoleEntity:
        data = RoleMapper.to_persistence(role)

        stmt = insert(ORMRole).values(**data).returning(ORMRole)
        result: Result = await self._session.execute(stmt)

        return RoleMapper.to_domain(result.scalar_one())

    async def add_permission(self, role_permission: RolePermissionEntity) -> None:
        data = RolePermissionMapper.to_persistence(role_permission)

        stmt = insert(ORMRolePermission).values(**data)
        await self._session.execute(stmt)

    async def remove_all_permissions(self) -> None:
        await self._session.execute(delete(ORMRolePermission))

    async def remove_all(self) -> None:
        await self._session.execute(delete(ORMRole))


class AccountRoleRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_permissions(self, account_id: str) -> frozenset[str]:
        result = await self._session.execute(
            select(ORMPermission.codename)
            .join(ORMRolePermission, ORMRolePermission.permission_id == ORMPermission.id)
            .join(ORMRole, ORMRole.id == ORMRolePermission.role_id)
            .join(ORMAccountRole, ORMAccountRole.role_id == ORMRole.id)
            .where(ORMAccountRole.account_id == account_id)
        )
        return frozenset(result.scalars().all())

    async def get_role_name(self, account_id: str) -> str | None:
        result = await self._session.execute(
            select(ORMRole.name)
            .join(ORMAccountRole, ORMAccountRole.role_id == ORMRole.id)
            .where(ORMAccountRole.account_id == account_id)
        )
        return result.scalar_one_or_none()

    async def exists(self, account_id: str) -> bool:
        stmt = select(exists().where(ORMAccountRole.account_id == account_id))
        result: Result = await self._session.execute(stmt)
        return result.scalar() or False

    async def create(self, account_role: AccountRoleEntity) -> None:
        """
        Чистый INSERT.
        ID уже должен быть в domain entity.
        """
        data = AccountRoleMapper.to_persistence(account_role)
        stmt = insert(ORMAccountRole).values(**data)
        await self._session.execute(stmt)

    async def update(self, account_role: AccountRoleEntity) -> None:
        """
        Чистый UPDATE.
        """
        stmt = (
            update(ORMAccountRole)
            .where(ORMAccountRole.account_id == account_role.account_id)
            .values(role_id=account_role.role_id)
        )
        await self._session.execute(stmt)
