"""
identity/application/permissions/service.py

PermissionService — application-сервис синхронизации прав.
"""

from __future__ import annotations

import logging

from identity.domain.entities.permission import Permission, Role
from identity.domain.services.permission_sync import PermissionSyncPolicy
from identity.infrastructure.permissions.role_cache import invalidate as invalidate_role_cache
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger("default")


class PermissionService:
    def __init__(self, uow_factory: IdentityUoWFactory) -> None:
        self._uow_factory = uow_factory
        self._sync_policy = PermissionSyncPolicy()

    async def sync_permissions(self) -> None:
        """
        Синхронизировать пермишены и роли из кода → БД.
        Идемпотентно: безопасно запускать при каждом старте.
        """
        logger.info("Синхронизация пермишенов и ролей...")

        permissions_to_sync = self._sync_policy.build_permissions()
        roles_to_sync = self._sync_policy.build_roles()

        async with self._uow_factory.create(master=True) as uow:
            synced_permissions = await uow.permissions.upsert_many(permissions_to_sync)
            perm_by_codename: dict[str, Permission] = {p.codename: p for p in synced_permissions}
            logger.info("Синхронизировано пермишенов: %d", len(synced_permissions))

            synced_roles = await uow.roles.upsert_many(roles_to_sync)
            logger.info("Синхронизировано ролей: %d", len(synced_roles))

            for role in synced_roles:
                codenames = self._sync_policy.get_role_permission_codenames(role)
                permission_ids = [perm_by_codename[cn].id for cn in codenames if cn in perm_by_codename]
                await uow.roles.set_permissions(role.id, permission_ids)

        invalidate_role_cache()
        logger.info("Синхронизация пермишенов завершена")

    async def get_all_permissions(self) -> list[Permission]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.permissions.get_all()

    async def get_all_roles(self) -> list[Role]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.roles.get_all()

    async def get_role_with_permissions(self, role_name: str) -> Role | None:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.roles.get_by_name_with_permissions(role_name)
