"""
infrastructure/permissions/repositories.py

Реализации репозиториев системы разрешений.

Ключевые решения:
- get_account_permissions использует один JOIN-запрос (не N+1)
- ensure_* методы идемпотентны (ON CONFLICT DO NOTHING)
- Все строковые операции идут через параметры, не f-строки
"""

from __future__ import annotations

from domain.entities.permission import PermissionEntity, RoleEntity
from domain.permissions.constants import role_permissions
from domain.permissions.enums import DefaultRole, Permission as PermissionEnum
from domain.repositories.permission import (
    AbstractAccountRoleRepository,
    AbstractPermissionRepository,
    AbstractRoleRepository,
)
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from domain.utils import generate_uuid
from infrastructure.common.repositories import BaseRepository
from infrastructure.db.models.permission import (
    AccountRole,
    Permission,
    Role,
    RolePermission,
)
from infrastructure.permissions.mapper import _map_permission, _map_role


class PermissionRepository(BaseRepository, AbstractPermissionRepository):
    async def get_all_permissions(self) -> list[PermissionEntity]:
        result = await self.session.execute(select(Permission))
        return [_map_permission(p) for p in result.scalars().all()]

    async def get_permission_by_codename(self, codename: str) -> PermissionEntity | None:
        result = await self.session.execute(
            select(Permission).where(Permission.codename == codename)
        )
        p = result.scalar_one_or_none()
        return _map_permission(p) if p else None

    async def create_permission(self, codename: str, description: str = "") -> PermissionEntity:
        stmt = (
            pg_insert(Permission)
            .values(id=generate_uuid(), codename=codename, description=description)
            .on_conflict_do_nothing(index_elements=["codename"])
            .returning(Permission)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return _map_permission(row)
        # Уже существует — достаём
        existing = await self.get_permission_by_codename(codename)
        return existing  # type: ignore[return-value]

    async def ensure_permissions_exist(self, codenames: list[str]) -> list[PermissionEntity]:
        if not codenames:
            return []

        rows = [{"id": generate_uuid(), "codename": c, "description": ""} for c in codenames]
        stmt = pg_insert(Permission).values(rows).on_conflict_do_nothing(index_elements=["codename"])
        await self.session.execute(stmt)

        result = await self.session.execute(
            select(Permission).where(Permission.codename.in_(codenames))
        )
        return [_map_permission(p) for p in result.scalars().all()]


class RoleRepository(BaseRepository, AbstractRoleRepository):
    async def get_all_roles(self) -> list[RoleEntity]:
        result = await self.session.execute(select(Role))
        return [_map_role(r) for r in result.scalars().all()]

    async def get_role_by_name(self, name: str) -> RoleEntity | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name)
        )
        r = result.scalar_one_or_none()
        return _map_role(r) if r else None

    async def get_role_with_permissions(self, name: str) -> RoleEntity | None:
        """Один запрос с JOIN вместо двух последовательных."""
        role_result = await self.session.execute(
            select(Role).where(Role.name == name)
        )
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

    async def create_role(self, name: str, description: str = "") -> RoleEntity:
        stmt = (
            pg_insert(Role)
            .values(id=generate_uuid(), name=name, description=description)
            .on_conflict_do_nothing(index_elements=["name"])
            .returning(Role)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return _map_role(row)
        existing = await self.get_role_by_name(name)
        return existing  # type: ignore[return-value]

    async def assign_permission_to_role(self, role_name: str, permission_codename: str) -> None:
        role = await self.get_role_by_name(role_name)
        perm_result = await self.session.execute(
            select(Permission).where(Permission.codename == permission_codename)
        )
        perm = perm_result.scalar_one_or_none()
        if not role or not perm:
            return

        stmt = (
            pg_insert(RolePermission)
            .values(id=generate_uuid(), role_id=role.id, permission_id=perm.id)
            .on_conflict_do_nothing()
        )
        await self.session.execute(stmt)

    async def revoke_permission_from_role(self, role_name: str, permission_codename: str) -> None:
        role = await self.get_role_by_name(role_name)
        perm_result = await self.session.execute(
            select(Permission).where(Permission.codename == permission_codename)
        )
        perm = perm_result.scalar_one_or_none()
        if not role or not perm:
            return

        await self.session.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id,
            )
        )

    async def set_role_permissions(self, role_name: str, permission_codenames: list[str]) -> RoleEntity:
        role = await self.get_role_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        # Достаём permission-объекты
        perm_result = await self.session.execute(
            select(Permission).where(Permission.codename.in_(permission_codenames))
        )
        perms = perm_result.scalars().all()

        # Удаляем все текущие
        await self.session.execute(
            delete(RolePermission).where(RolePermission.role_id == role.id)
        )

        # Вставляем новые
        if perms:
            rows = [
                {"id": generate_uuid(), "role_id": role.id, "permission_id": p.id}
                for p in perms
            ]
            await self.session.execute(pg_insert(RolePermission).values(rows).on_conflict_do_nothing())

        return await self.get_role_with_permissions(role_name)  # type: ignore[return-value]

    async def ensure_default_roles_exist(self) -> None:
        """
        Идемпотентная инициализация системных ролей при старте.
        Вызывается из lifespan FastAPI.
        """

        all_codenames = list({c for perms in role_permissions.values() for c in perms})
        perm_repo = PermissionRepository(self.session)
        await perm_repo.ensure_permissions_exist(all_codenames)

        for role_name, codenames in role_permissions.items():
            await self.create_role(name=role_name, description=f"System role: {role_name}")
            await self.set_role_permissions(role_name, codenames)


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
        role_result = await self.session.execute(
            select(Role).where(Role.name == role_name)
        )
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
