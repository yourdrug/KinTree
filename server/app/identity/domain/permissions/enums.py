"""
domain/permissions/enums.py

Единственный источник правды о том, КАКИЕ пермишены существуют в системе.

DDD-принципы:
- Enum — константы домена, не инфраструктура.
- БД хранит только то, КОМУ назначены пермишены.
- Добавил пермишен в enum → создал Alembic-миграцию → задеплоил.
- Никакого автосинка во время HTTP-запросов — изменения явные, версионированные.

Соглашение по именованию codename: resource:action[:scope]
Примеры: "family:read", "family:delete:own", "family:delete:any"
"""

from __future__ import annotations

from enum import Enum


class PermissionCodename(str, Enum):
    """
    Все пермишены приложения.

    Значение (value) — строка которая хранится в БД и JWT.
    description — человекочитаемое описание для UI и документации.
    """

    description: str

    def __new__(cls, value: str, description: str) -> PermissionCodename:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    # ── Семьи ─────────────────────────────────────────────────────────────────
    FAMILY__READ = ("family:read", "Просмотр семей")
    FAMILY__CREATE = ("family:create", "Создание семей")
    FAMILY__UPDATE_OWN = ("family:update:own", "Редактирование своей семьи")
    FAMILY__DELETE_OWN = ("family:delete:own", "Удаление своей семьи")
    FAMILY__UPDATE_ANY = ("family:update:any", "Редактирование любой семьи")
    FAMILY__DELETE_ANY = ("family:delete:any", "Удаление любой семьи")

    # ── Персоны ───────────────────────────────────────────────────────────────
    PERSON__READ = ("person:read", "Просмотр персон")
    PERSON__CREATE = ("person:create", "Создание персон")
    PERSON__UPDATE_OWN = ("person:update:own", "Редактирование своих персон")
    PERSON__DELETE_OWN = ("person:delete:own", "Удаление своих персон")
    PERSON__UPDATE_ANY = ("person:update:any", "Редактирование любой персоны")
    PERSON__DELETE_ANY = ("person:delete:any", "Удаление любой персоны")

    # ── Связи ─────────────────────────────────────────────────────────────────
    RELATION__CREATE = ("relation:create", "Создание связей между персонами")
    RELATION__DELETE = ("relation:delete", "Удаление связей между персонами")

    # ── Аккаунты ──────────────────────────────────────────────────────────────
    ACCOUNT__READ_SELF = ("account:read:own", "Просмотр своего аккаунта")
    ACCOUNT__READ_ANY = ("account:read:any", "Просмотр любого аккаунта")
    ACCOUNT__BLOCK = ("account:block", "Блокировка аккаунта")
    ACCOUNT__DELETE = ("account:delete", "Удаление аккаунта")

    # ── Администрирование ─────────────────────────────────────────────────────
    ADMIN__PANEL = ("admin:panel", "Доступ к панели администратора")
    ADMIN__MANAGE_ROLES = ("admin:manage_roles", "Управление ролями пользователей")


class RoleName(str, Enum):
    """
    Системные роли. Создаются один раз при инициализации БД.
    Новые роли добавляются через Alembic-миграцию.
    """

    description: str | None

    def __new__(cls, value: str, description: str | None = None) -> RoleName:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = description
        return obj

    GUEST = ("guest", "Только чтение публичных данных")
    USER = ("user", "Базовые операции со своими данными")
    MODERATOR = ("moderator", "Расширенные права на управление контентом")
    ADMIN = ("admin", "Полные права")
