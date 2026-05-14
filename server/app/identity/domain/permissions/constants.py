"""
domain/permissions/constants.py

Маппинг роль → набор пермишенов.

Вместе с enums.py образует полный источник правды о правах в коде.

При добавлении нового пермишена:
  1. Добавить codename в PermissionCodename (enums.py)
  2. Добавить описание в PERMISSION_DESCRIPTIONS (этот файл)
  3. Добавить в нужные роли в ROLE_PERMISSIONS (этот файл)
  4. Создать Alembic-миграцию
  5. Задеплоить — PermissionSyncService синхронизирует БД при старте

"""

from __future__ import annotations

from identity.domain.permissions.enums import PermissionCodename, RoleName


# ── Маппинг роль → пермишены ──────────────────────────────────────────────────
# Единственное место, где определяется «кто что может».
# Изменение здесь + миграция = изменение прав в системе.

ROLE_PERMISSIONS: dict[RoleName, list[PermissionCodename]] = {
    RoleName.GUEST: [
        PermissionCodename.FAMILY__READ,
        PermissionCodename.PERSON__READ,
    ],
    RoleName.USER: [
        # Семьи
        PermissionCodename.FAMILY__READ,
        PermissionCodename.FAMILY__CREATE,
        PermissionCodename.FAMILY__UPDATE_OWN,
        PermissionCodename.FAMILY__DELETE_OWN,
        # Персоны
        PermissionCodename.PERSON__READ,
        PermissionCodename.PERSON__CREATE,
        PermissionCodename.PERSON__UPDATE_OWN,
        PermissionCodename.PERSON__DELETE_OWN,
        # Связи
        PermissionCodename.RELATION__CREATE,
        PermissionCodename.RELATION__DELETE,
        # Аккаунт
        PermissionCodename.ACCOUNT__READ_SELF,
    ],
    RoleName.MODERATOR: [
        # Семьи
        PermissionCodename.FAMILY__READ,
        PermissionCodename.FAMILY__CREATE,
        PermissionCodename.FAMILY__UPDATE_OWN,
        PermissionCodename.FAMILY__DELETE_OWN,
        PermissionCodename.FAMILY__UPDATE_ANY,
        # Персоны
        PermissionCodename.PERSON__READ,
        PermissionCodename.PERSON__CREATE,
        PermissionCodename.PERSON__UPDATE_OWN,
        PermissionCodename.PERSON__DELETE_OWN,
        PermissionCodename.PERSON__UPDATE_ANY,
        PermissionCodename.PERSON__DELETE_ANY,
        # Связи
        PermissionCodename.RELATION__CREATE,
        PermissionCodename.RELATION__DELETE,
        # Аккаунты
        PermissionCodename.ACCOUNT__READ_SELF,
        PermissionCodename.ACCOUNT__READ_ANY,
    ],
    RoleName.ADMIN: list(PermissionCodename),  # все пермишены
}
