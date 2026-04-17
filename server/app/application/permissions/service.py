"""
application/permissions/service.py

Сервис управления ролями и разрешениями.
Все данные о разрешениях и ролях берутся исключительно из БД.
"""

from __future__ import annotations

from domain.entities.permission import PermissionEntity, RoleEntity, AccountRoleEntity
from domain.exceptions import NotFoundValidationError
from infrastructure.common.services import BaseService


class PermissionService(BaseService):

    async def get_all_permissions(self) -> list[PermissionEntity]:
        async with self.uow:
            return await self.repository_facade.permission_repository.get_all_permissions()

    async def get_permission_by_codename(self, codename: str) -> PermissionEntity | None:
        async with self.uow:
            return await self.repository_facade.permission_repository.get_permission_or_none(codename)

    async def get_all_roles(self) -> list[RoleEntity]:
        async with self.uow:
            return await self.repository_facade.role_repository.get_all_roles()

    async def get_role_with_permissions(self, role_name: str) -> RoleEntity | None:
        async with self.uow:
            return await self.repository_facade.role_repository.get_role_with_permissions(role_name)

    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        async with self.uow:
            return await self.repository_facade.account_role_repository.get_account_permissions(account_id=account_id)

    async def get_account_role_name(self, account_id: str) -> str:
        async with self.uow:
            return await self.repository_facade.account_role_repository.get_account_role_name(account_id=account_id)
