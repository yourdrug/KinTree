"""
application/permissions/service.py

Application-сервис системы разрешений.

Отвечает за:
1. Синхронизацию пермишенов и ролей с БД при старте (sync_permissions).
2. Запросы к хранилищу ролей и пермишенов.

Синхронизация при старте:
  Идемпотентная операция. Запускается в lifespan FastAPI.
  Алгоритм:
    1. Upsert всех Permission из кода в БД.
    2. Upsert всех Role из кода в БД.
    3. Для каждой роли: set_permissions (полная замена).
"""

from __future__ import annotations

import logging

from identity.domain.entities.permission import Permission, Role
from identity.domain.services.permission_sync import PermissionSyncService
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger("default")


class PermissionService:
    """Application-сервис управления пермишенами и ролями."""

    def __init__(self, uow_factory: IdentityUoWFactory) -> None:
        self._uow_factory = uow_factory
        self._sync_service = PermissionSyncService()

    async def sync_permissions(self) -> None:
        """
        Синхронизировать пермишены и роли из кода → БД.

        Идемпотентно: безопасно запускать при каждом старте.
        Запускается из lifespan FastAPI ПОСЛЕ миграций.

        Raises:
            Exception: пробрасывает любую ошибку БД — старт завершится неудачей.
        """
        logger.info("Синхронизация пермишенов и ролей...")

        permissions_to_sync: list[Permission] = self._sync_service.build_permissions()
        roles_to_sync: list[Role] = self._sync_service.build_roles()

        async with self._uow_factory.create(master=True) as uow:
            synced_permissions: list[Permission] = await uow.permissions.upsert_many(permissions_to_sync)
            perm_by_codename: dict[str, Permission] = {p.codename: p for p in synced_permissions}

            logger.info(f"Синхронизировано пермишенов: {len(synced_permissions)}")

            synced_roles: list[Role] = await uow.roles.upsert_many(roles_to_sync)

            logger.info(f"Синхронизировано ролей: {len(synced_roles)}")

            for role in synced_roles:
                codenames: list[str] = self._sync_service.get_role_permission_codenames(role.name)
                permission_ids: list[str] = [perm_by_codename[cn].id for cn in codenames if cn in perm_by_codename]
                await uow.roles.set_permissions(role.id, permission_ids)

            logger.info("Синхронизация пермишенов завершена успешно")

    async def get_all_permissions(self) -> list[Permission]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.permissions.get_all()

    async def get_all_roles(self) -> list[Role]:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.roles.get_all()

    async def get_role_with_permissions(self, role_name: str) -> Role | None:
        async with self._uow_factory.create(master=False) as uow:
            return await uow.roles.get_by_name_with_permissions(role_name)
