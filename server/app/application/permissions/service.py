"""
application/permissions/service.py

Сервис управления ролями и разрешениями.
Все данные о разрешениях и ролях берутся исключительно из БД.
"""

from __future__ import annotations

from domain.entities.permission import PermissionEntity, RoleEntity

from application.uow_factory import UoWFactory


class PermissionService:
    def __init__(self, uow_factory: UoWFactory) -> None:
        self._uow_factory = uow_factory

    async def get_all_permissions(self) -> list[PermissionEntity]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.permissions.get_all()

    async def get_permission_by_codename(self, codename: str) -> PermissionEntity | None:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.permissions.get_by_codename(codename)

    async def get_all_roles(self) -> list[RoleEntity]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.roles.get_all()

    async def get_role_with_permissions(self, role_name: str) -> RoleEntity | None:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.roles.get_with_permissions(role_name)

    async def get_account_permissions(self, account_id: str) -> frozenset[str]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.account_roles.get_permissions(account_id=account_id)

    async def get_account_role_name(self, account_id: str) -> str | None:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.account_roles.get_role_name(account_id=account_id)
