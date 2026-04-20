"""
cli/commands/upload_roles_and_permissions.py

CLI-команда: полная пересинхронизация ролей и пермишенов.

Отличие от автосинка при старте (sync_permissions):
- Эта команда делает ПОЛНЫЙ СБРОС: удаляет всё и создаёт заново.
- Используется для ручного восстановления или при деплоях
  где нужно явно сбросить накопившиеся «мусорные» данные.

Автосинк при старте (lifespan) делает МЯГКИЙ upsert:
- Не удаляет существующие данные.
- Только добавляет новое и обновляет описания.

Когда использовать эту команду:
  make upload-roles-permissions
"""

from __future__ import annotations

import logging
import sys

from application.uow_factory import UoWFactory
from domain.entities.permission import create_permission, create_role
from domain.permissions.constants import (
    PERMISSION_DESCRIPTIONS,
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
)
from domain.permissions.enums import PermissionCodename, RoleName


logger = logging.getLogger("default")


async def upload_roles_and_permissions(uow_factory: UoWFactory) -> None:
    """
    Полная пересинхронизация: удалить всё → создать заново.

    Алгоритм:
      1. Удалить все role_permissions (M2M связи)
      2. Удалить все account_roles (чтобы снять FK)
         — НЕ удаляем! Это приведёт к потере связей аккаунт-роль.
         Вместо этого пересоздаём роли с теми же name — FK не сломается.
      3. Пересоздать permissions (upsert по codename)
      4. Пересоздать roles (upsert по name)
      5. Установить связи role → permissions

    FK account_roles.role_id → roles.id сохраняется, потому что
    мы делаем upsert по name, а не delete+insert.
    """
    logger.info("Загрузка ролей и пермишенов (полная пересинхронизация)...")

    try:
        async with uow_factory.create(master=True) as uow:
            # --- 1. Очистить связи роль-пермишен ---
            await uow.roles.remove_all_role_permissions()
            logger.info("Связи роль-пермишен очищены")

            # --- 2. Upsert пермишенов ---
            permissions_to_create = [
                create_permission(
                    codename=perm.value,
                    description=PERMISSION_DESCRIPTIONS.get(perm, ""),
                )
                for perm in PermissionCodename
            ]
            synced_permissions = await uow.permissions.upsert_many(permissions_to_create)
            perm_by_codename = {p.codename: p for p in synced_permissions}
            logger.info(f"Пермишены: {len(synced_permissions)} синхронизировано")

            # --- 3. Upsert ролей ---
            roles_to_create = [
                create_role(
                    name=role.value,
                    description=ROLE_DESCRIPTIONS.get(role, ""),
                )
                for role in RoleName
            ]
            synced_roles = await uow.roles.upsert_many(roles_to_create)
            logger.info(f"Роли: {len(synced_roles)} синхронизировано")

            # --- 4. Установить связи роль → пермишены ---
            for role in synced_roles:
                try:
                    role_enum = RoleName(role.name, role.description)
                except ValueError:
                    logger.warning(f"Роль '{role.name}' не найдена в RoleName enum, пропускаем")
                    continue

                codenames = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
                permission_ids = [perm_by_codename[cn].id for cn in codenames if cn in perm_by_codename]
                await uow.roles.set_permissions(role.id, permission_ids)
                logger.info(f"Роль '{role.name}': назначено {len(permission_ids)} пермишенов")

    except Exception as exc:
        logger.error("Ошибка при загрузке ролей и пермишенов", exc_info=exc)
        sys.exit(1)
    else:
        logger.info("Роли и пермишены успешно загружены")
