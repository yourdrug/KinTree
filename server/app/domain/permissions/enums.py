"""
domain/permissions/enums.py

Строковые перечисления разрешений и ролей.
Хранятся в БД как VARCHAR — миграции при добавлении новых значений не нужны.

Соглашение: RESOURCE__ACTION
"""

from enum import Enum


class Permission(str, Enum):
    # ── Семьи ──────────────────────────────────────────────────────────────
    FAMILY__READ = "family:read"
    FAMILY__CREATE = "family:create"
    FAMILY__UPDATE_OWN = "family:update_own"
    FAMILY__DELETE_OWN = "family:delete_own"
    FAMILY__UPDATE_ANY = "family:update_any"
    FAMILY__DELETE_ANY = "family:delete_any"

    # ── Персоны ────────────────────────────────────────────────────────────
    PERSON__READ = "person:read"
    PERSON__CREATE = "person:create"
    PERSON__UPDATE_OWN = "person:update_own"
    PERSON__DELETE_OWN = "person:delete_own"
    PERSON__UPDATE_ANY = "person:update_any"
    PERSON__DELETE_ANY = "person:delete_any"

    # ── Аккаунты ───────────────────────────────────────────────────────────
    ACCOUNT__READ_SELF = "account:read_self"
    ACCOUNT__READ_ANY = "account:read_any"
    ACCOUNT__BLOCK = "account:block"
    ACCOUNT__DELETE = "account:delete"

    # ── Администрирование ──────────────────────────────────────────────────
    ADMIN__PANEL = "admin:panel"
    ADMIN__MANAGE_ROLES = "admin:manage_roles"


class DefaultRole(str, Enum):
    """
    Предопределённые системные роли.
    При старте приложения проверяется/создаётся их наличие в БД.
    """

    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
