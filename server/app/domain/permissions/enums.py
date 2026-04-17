"""
domain/permissions/enums.py

Строковые перечисления разрешений и ролей.
Хранятся в БД как VARCHAR — миграции при добавлении новых значений не нужны.

Соглашение: RESOURCE__ACTION
"""

from enum import Enum


class Permission(str, Enum):
    description: str

    def __new__(cls, value: str, description: str) -> "Permission":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    # ── Семьи ─────────────────────────────────────────
    FAMILY__READ = ("family:read", "Чтение семей")
    FAMILY__CREATE = ("family:create", "Создание семей")
    FAMILY__UPDATE_OWN = ("family:update:own", "Обновление своей семьи")
    FAMILY__DELETE_OWN = ("family:delete:own", "Удаление своей семьи")
    FAMILY__UPDATE_ANY = ("family:update:any", "Обновление любой семьи")
    FAMILY__DELETE_ANY = ("family:delete:any", "Удаление любой семьи")

    # ── Персоны ───────────────────────────────────────
    PERSON__READ = ("person:read", "Чтение персон")
    PERSON__CREATE = ("person:create", "Создание персон")
    PERSON__UPDATE_OWN = ("person:update:own", "Обновление своей персоны")
    PERSON__DELETE_OWN = ("person:delete:own", "Удаление своей персоны")
    PERSON__UPDATE_ANY = ("person:update:any", "Обновление любой персоны")
    PERSON__DELETE_ANY = ("person:delete:any", "Удаление любой персоны")

    # ── Аккаунты ──────────────────────────────────────
    ACCOUNT__READ_SELF = ("account:read:own", "Чтение своего аккаунта")
    ACCOUNT__READ_ANY = ("account:read:any", "Чтение любого аккаунта")
    ACCOUNT__BLOCK = ("account:block", "Блокировка аккаунта")
    ACCOUNT__DELETE = ("account:delete", "Удаление аккаунта")

    # ── Админка ───────────────────────────────────────
    ADMIN__PANEL = ("admin:panel", "Доступ к админ панели")
    ADMIN__MANAGE_ROLES = ("admin:manage_roles", "Управление ролями")


class DefaultRole(str, Enum):
    """
    Предопределённые системные роли.
    При старте приложения проверяется/создаётся их наличие в БД.
    """

    description: str

    def __new__(cls, value: str, description: str) -> "DefaultRole":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    GUEST = ("guest", "Только чтение публичных данных")
    USER = ("user", "Базовые операции со своими данными")
    MODERATOR = ("moderator", "Расширенные права на управление контентом")
    ADMIN = ("admin", "Полные права")
