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

from identity.application.permissions.service import PermissionService
from shared.infrastructure.db.database import database
from identity.infrastructure.uow_factory import IdentityUoWFactory


logger = logging.getLogger("default")


async def upload_roles_and_permissions() -> None:
    logger.info("Загрузка ролей и пермишенов (полная пересинхронизация)...")

    try:
        uow_factory = IdentityUoWFactory(database)
        service = PermissionService(uow_factory)
        await service.sync_permissions()
    except Exception as exc:
        logger.error("Ошибка при загрузке ролей и пермишенов", exc_info=exc)
        sys.exit(1)
    else:
        logger.info("Роли и пермишены успешно загружены")
