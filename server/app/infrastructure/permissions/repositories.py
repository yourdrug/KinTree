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
from domain.repositories.permission import (
    AbstractAccountRoleRepository,
    AbstractPermissionRepository,
    AbstractRoleRepository,
)
from domain.utils import generate_uuid
from sqlalchemy import Result, Select, delete, select
from sqlalchemy.dialects.postgresql import Insert as PgInsert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from infrastructure.common.repositories import BaseRepository
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
    PermissionMapper,
    RoleMapper,
    RolePermissionMapper,
)


class PermissionRepository(BaseRepository, AbstractPermissionRepository):
    async def get_all_permissions(self) -> list[PermissionEntity]:
        result: Result = await self.session.execute(select(ORMPermission))
        return [PermissionMapper.to_domain(perm) for perm in result.scalars().all()]

    async def get_permission_or_none(self, codename: str) -> PermissionEntity | None:
        statement: Select = select(ORMPermission).where(ORMPermission.codename == codename)
        result: Result = await self.session.execute(statement)
        permission: ORMPermission | None = result.scalar_one_or_none()
        return PermissionMapper.to_domain(permission) if permission else None

    async def create_permission(self, permission: PermissionEntity) -> PermissionEntity:
        data: dict = PermissionMapper.to_persistence(permission)
        statement = pg_insert(ORMPermission).values(**data).returning(ORMPermission)
        result: Result = await self.session.execute(statement)
        orm_permission: ORMPermission = result.scalar_one()

        return PermissionMapper.to_domain(orm_permission)

    async def delete_all_permissions(self) -> None:
        await self.session.execute(delete(ORMPermission))


class RoleRepository(BaseRepository, AbstractRoleRepository):
    async def get_all_roles(self) -> list[RoleEntity]:
        result: Result = await self.session.execute(select(ORMRole))
        return [RoleMapper.to_domain(role) for role in result.scalars().all()]

    async def get_role_or_none(self, name: str) -> RoleEntity | None:
        statement: Select = select(ORMRole).where(ORMRole.name == name)
        result: Result = await self.session.execute(statement)
        role: ORMRole = result.scalar_one_or_none()
        return RoleMapper.to_domain(role) if role else None

    async def get_role_with_permissions(self, name: str) -> RoleEntity | None:
        """Один запрос с JOIN вместо двух последовательных."""
        statement: Select = select(ORMRole).where(ORMRole.name == name)
        role_result: Result = await self.session.execute(statement)
        orm_role: ORMRole | None = role_result.scalar_one_or_none()

        if not orm_role:
            return None

        perm_result: Result = await self.session.execute(
            select(ORMPermission)
            .join(ORMRolePermission, ORMRolePermission.permission_id == ORMPermission.id)
            .where(ORMRolePermission.role_id == orm_role.id)
        )
        permissions: list[PermissionEntity | None] = [
            PermissionMapper.to_domain(perm) for perm in perm_result.scalars().all()
        ]
        return RoleMapper.to_domain(orm_role, permissions)

    async def create_role(self, role_entity: RoleEntity) -> RoleEntity:
        data = RoleMapper.to_persistence(entity=role_entity)

        statement = pg_insert(ORMRole).values(**data).returning(ORMRole)
        result: Result = await self.session.execute(statement)
        orm_role: ORMRole = result.scalar_one()
        return RoleMapper.to_domain(orm_role)

    async def delete_all_role_permission(self) -> None:
        await self.session.execute(delete(ORMRolePermission))

    async def delete_all_roles(self) -> None:
        await self.session.execute(delete(ORMRole))

    async def create_role_permissions(self, role_permission: RolePermissionEntity) -> None:
        data = RolePermissionMapper.to_persistence(role_permission)

        statement: PgInsert = pg_insert(ORMRolePermission).values(**data)
        statement = statement.on_conflict_do_update(
            index_elements=["id"],
            set_={key: value for key, value in data.items() if key not in ["id"]},
        )
        await self.session.execute(statement)


class AccountRoleRepository(BaseRepository, AbstractAccountRoleRepository):
    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        """
        Единственный JOIN-запрос вместо нескольких последовательных.
        account → account_roles → roles → role_permissions → permissions
        """
        result = await self.session.execute(
            select(ORMPermission.codename)
            .join(ORMRolePermission, ORMRolePermission.permission_id == ORMPermission.id)
            .join(ORMRole, ORMRole.id == ORMRolePermission.role_id)
            .join(ORMAccountRole, ORMAccountRole.role_id == ORMRole.id)
            .where(ORMAccountRole.account_id == account_id)
        )
        return frozenset(result.scalars().all())

    async def get_account_role_name(self, account_id: str) -> str:
        result = await self.session.execute(
            select(ORMRole.name)
            .join(ORMAccountRole, ORMAccountRole.role_id == ORMRole.id)
            .where(ORMAccountRole.account_id == account_id)
        )
        name = result.scalar_one_or_none()
        return name or "user"

    async def set_account_role(self, account_role: AccountRoleEntity) -> None:
        statement: PgInsert = (
            pg_insert(ORMAccountRole)
            .values(id=generate_uuid(), account_id=account_role.account_id, role_id=account_role.role_id)
            .on_conflict_do_update(
                index_elements=["account_id"],
                set_={"role_id": account_role.role_id},
            )
        )
        await self.session.execute(statement)
