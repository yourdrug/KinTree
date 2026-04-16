"""
application/permissions/service.py

Сервис управления ролями и разрешениями.
"""

from __future__ import annotations

from domain.entities.permission import PermissionEntity, RoleEntity
from infrastructure.common.services import BaseService


class PermissionService(BaseService):
    # ── Разрешения ─────────────────────────────────────────────────────────

    async def get_all_permissions(self) -> list[PermissionEntity]:
        async with self.uow:
            return await self.repository_facade.permission_repository.get_all_permissions()

    # ── Роли ───────────────────────────────────────────────────────────────

    async def get_all_roles(self) -> list[RoleEntity]:
        async with self.uow:
            return await self.repository_facade.role_repository.get_all_roles()

    async def get_role_with_permissions(self, role_name: str) -> RoleEntity | None:
        async with self.uow:
            return await self.repository_facade.role_repository.get_role_with_permissions(role_name)

    # async def create_role(self, name: str, description: str = "") -> RoleEntity:
    #     async with self.uow:
    #         return await self.repository_facade.role_repository.create_role(name=name, description=description)

    # ── Аккаунты ───────────────────────────────────────────────────────────

    async def set_account_role(self, account_id: str, role_name: str) -> None:
        async with self.uow:
            await self.repository_facade.account_role_repository.set_account_role(
                account_id=account_id, role_name=role_name
            )

    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        async with self.uow:
            return await self.repository_facade.account_role_repository.get_account_permissions(account_id=account_id)
