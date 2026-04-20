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

DDD-принцип: «кто что может» — это бизнес-правило домена, не конфигурация.
"""

from __future__ import annotations

from domain.permissions.enums import PermissionCodename, RoleName


# ── Описания пермишенов ───────────────────────────────────────────────────────
# Единственное место для человекочитаемых описаний.
# Используется при синхронизации с БД.

PERMISSION_DESCRIPTIONS: dict[PermissionCodename, str] = {
    # Семьи
    PermissionCodename.FAMILY__READ: "Просмотр семей",
    PermissionCodename.FAMILY__CREATE: "Создание семей",
    PermissionCodename.FAMILY__UPDATE_OWN: "Редактирование своей семьи",
    PermissionCodename.FAMILY__DELETE_OWN: "Удаление своей семьи",
    PermissionCodename.FAMILY__UPDATE_ANY: "Редактирование любой семьи",
    PermissionCodename.FAMILY__DELETE_ANY: "Удаление любой семьи",
    # Персоны
    PermissionCodename.PERSON__READ: "Просмотр персон",
    PermissionCodename.PERSON__CREATE: "Создание персон",
    PermissionCodename.PERSON__UPDATE_OWN: "Редактирование своих персон",
    PermissionCodename.PERSON__DELETE_OWN: "Удаление своих персон",
    PermissionCodename.PERSON__UPDATE_ANY: "Редактирование любой персоны",
    PermissionCodename.PERSON__DELETE_ANY: "Удаление любой персоны",
    # Связи
    PermissionCodename.RELATION__CREATE: "Создание связей между персонами",
    PermissionCodename.RELATION__DELETE: "Удаление связей между персонами",
    # Аккаунты
    PermissionCodename.ACCOUNT__READ_SELF: "Просмотр своего аккаунта",
    PermissionCodename.ACCOUNT__READ_ANY: "Просмотр любого аккаунта",
    PermissionCodename.ACCOUNT__BLOCK: "Блокировка аккаунта",
    PermissionCodename.ACCOUNT__DELETE: "Удаление аккаунта",
    # Администрирование
    PermissionCodename.ADMIN__PANEL: "Доступ к панели администратора",
    PermissionCodename.ADMIN__MANAGE_ROLES: "Управление ролями пользователей",
}

# ── Описания ролей ────────────────────────────────────────────────────────────

ROLE_DESCRIPTIONS: dict[RoleName, str] = {
    RoleName.GUEST: "Только чтение публичных данных",
    RoleName.USER: "Базовые операции со своими данными",
    RoleName.MODERATOR: "Расширенные права на управление контентом",
    RoleName.ADMIN: "Полные права",
}

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
