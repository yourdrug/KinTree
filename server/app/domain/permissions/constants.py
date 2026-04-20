"""
domain/permissions/constants.py

Маппинг роль → пермишены.
Вместе с enums.py образует полный источник правды в коде.

При добавлении нового пермишена:
1. Добавить в Permission enum (enums.py)
2. Добавить в нужные роли здесь
3. Создать Alembic-миграцию (см. шаблон в infrastructure/db/migrations/)
4. Задеплоить

Alembic-миграция синхронизирует БД с этим файлом.
"""

from __future__ import annotations

from domain.permissions.enums import DefaultRole, Permission


# Единственное место где определяется "кто что может"
role_permissions: dict[DefaultRole, list[Permission]] = {
    DefaultRole.GUEST: [
        Permission.FAMILY__READ,
        Permission.PERSON__READ,
    ],
    DefaultRole.USER: [
        # Семьи
        Permission.FAMILY__READ,
        Permission.FAMILY__CREATE,
        Permission.FAMILY__UPDATE_OWN,
        Permission.FAMILY__DELETE_OWN,
        # Персоны
        Permission.PERSON__READ,
        Permission.PERSON__CREATE,
        Permission.PERSON__UPDATE_OWN,
        Permission.PERSON__DELETE_OWN,
        # Связи
        Permission.RELATION__CREATE,
        Permission.RELATION__DELETE,
        # Аккаунт
        Permission.ACCOUNT__READ_SELF,
    ],
    DefaultRole.MODERATOR: [
        # Семьи
        Permission.FAMILY__READ,
        Permission.FAMILY__CREATE,
        Permission.FAMILY__UPDATE_OWN,
        Permission.FAMILY__DELETE_OWN,
        Permission.FAMILY__UPDATE_ANY,
        # Персоны
        Permission.PERSON__READ,
        Permission.PERSON__CREATE,
        Permission.PERSON__UPDATE_OWN,
        Permission.PERSON__DELETE_OWN,
        Permission.PERSON__UPDATE_ANY,
        Permission.PERSON__DELETE_ANY,
        # Связи
        Permission.RELATION__CREATE,
        Permission.RELATION__DELETE,
        # Аккаунты
        Permission.ACCOUNT__READ_SELF,
        Permission.ACCOUNT__READ_ANY,
    ],
    DefaultRole.ADMIN: list(Permission),  # все пермишены
}
