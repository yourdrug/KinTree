"""
infrastructure/permissions/repositories.py

Реализации репозиториев системы разрешений.

Ключевые решения:
- get_account_permissions использует один JOIN-запрос (не N+1)
- ensure_* методы идемпотентны (ON CONFLICT DO NOTHING)
- Все строковые операции идут через параметры, не f-строки
"""

from __future__ import annotations

from domain.entities.permission import PermissionEntity, RoleEntity, RolePermissionEntity
from domain.permissions.enums import DefaultRole
from domain.repositories.permission import (
    AbstractAccountRoleRepository,
    AbstractPermissionRepository,
    AbstractRoleRepository,
)
from domain.utils import generate_uuid
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import Insert as PgInsert
from sqlalchemy.dialects.postgresql import insert as pg_insert

from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.permission import (
    AccountRole,
    Permission,
    Role,
    RolePermission,
)
from infrastructure.permissions.mapper import (
    PermissionMapper,
    RoleMapper,
    RolePermissionMapper,
    _map_permission,
    _map_role,
)


class PermissionRepository(BaseRepository, AbstractPermissionRepository):
    async def get_all_permissions(self) -> list[PermissionEntity]:
        result = await self.session.execute(select(Permission))
        return [_map_permission(p) for p in result.scalars().all()]

    async def get_permission_by_codename(self, codename: str) -> PermissionEntity | None:
        result = await self.session.execute(select(Permission).where(Permission.codename == codename))
        p = result.scalar_one_or_none()
        return _map_permission(p) if p else None

    async def create_permission(self, permission: PermissionEntity) -> PermissionEntity:
        data = PermissionMapper.to_persistence(permission)

        stmt = (
            pg_insert(Permission)
            .values(**data)
            .on_conflict_do_nothing(index_elements=["codename"])
            .returning(Permission)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return _map_permission(row)
        # Уже существует — достаём
        existing = await self.get_permission_by_codename(permission.codename)
        return existing  # type: ignore[return-value]

    async def ensure_permissions_exist(self, codenames: list[str]) -> list[PermissionEntity]:
        if not codenames:
            return []

        rows = [{"id": generate_uuid(), "codename": c, "description": ""} for c in codenames]
        stmt = pg_insert(Permission).values(rows).on_conflict_do_nothing(index_elements=["codename"])
        await self.session.execute(stmt)

        result = await self.session.execute(select(Permission).where(Permission.codename.in_(codenames)))
        return [_map_permission(p) for p in result.scalars().all()]


class RoleRepository(BaseRepository, AbstractRoleRepository):
    async def get_all_roles(self) -> list[RoleEntity]:
        result = await self.session.execute(select(Role))
        return [_map_role(r) for r in result.scalars().all()]

    async def get_role_by_name(self, name: str) -> RoleEntity | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        r = result.scalar_one_or_none()
        return _map_role(r) if r else None

    async def get_role_with_permissions(self, name: str) -> RoleEntity | None:
        """Один запрос с JOIN вместо двух последовательных."""
        role_result = await self.session.execute(select(Role).where(Role.name == name))
        role = role_result.scalar_one_or_none()
        if not role:
            return None

        perm_result = await self.session.execute(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
        )
        permissions = [_map_permission(p) for p in perm_result.scalars().all()]
        return _map_role(role, permissions)

    async def create_role(self, role_entity: RoleEntity) -> RoleEntity:
        data = RoleMapper.to_persistence(entity=role_entity)

        stmt = pg_insert(Role).values(**data).on_conflict_do_nothing(index_elements=["name"]).returning(Role)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return _map_role(row)
        existing = await self.get_role_by_name(role_entity.name)
        return existing  # type: ignore[return-value]

    async def delete_all_role_permission(self) -> None:
        await self.session.execute(delete(RolePermission))

    async def insert_or_update(self, role_permission: RolePermissionEntity) -> None:
        data = RolePermissionMapper.to_persistence(role_permission)

        statement: PgInsert = pg_insert(RolePermission).values(**data)
        statement = statement.on_conflict_do_update(
            index_elements=["id"],
            set_={key: value for key, value in data.items() if key not in ["id"]},
        )
        await self.session.execute(statement)

        return None


class AccountRoleRepository(BaseRepository, AbstractAccountRoleRepository):
    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        """
        Единственный JOIN-запрос вместо нескольких последовательных.
        account → account_roles → roles → role_permissions → permissions
        """
        result = await self.session.execute(
            select(Permission.codename)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        return frozenset(result.scalars().all())

    async def get_account_role_name(self, account_id: str) -> str:
        result = await self.session.execute(
            select(Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
        )
        name = result.scalar_one_or_none()
        return name or DefaultRole.USER

    async def set_account_role(self, account_id: str, role_name: str) -> None:
        role_result = await self.session.execute(select(Role).where(Role.name == role_name))
        role = role_result.scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{role_name}' not found in database")

        stmt = (
            pg_insert(AccountRole)
            .values(id=generate_uuid(), account_id=account_id, role_id=role.id)
            .on_conflict_do_update(
                index_elements=["account_id"],
                set_={"role_id": role.id},
            )
        )
        await self.session.execute(stmt)
