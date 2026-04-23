"""
domain/services/permission_sync.py

Доменный сервис синхронизации пермишенов.

DDD-принципы:
- Доменный сервис содержит логику, которая не принадлежит одной Entity.
- Он знает о domain-константах (PermissionCodename, ROLE_PERMISSIONS).
- Он НЕ знает о БД, HTTP, Pydantic.
- Возвращает доменные объекты.

Назначение:
  При старте приложения убеждаемся, что в БД есть все пермишены
  и роли, объявленные в коде. Это идемпотентная операция —
  запускать можно сколько угодно раз.

Алгоритм:
  1. Собрать все Permission-объекты из enum.
  2. Upsert в БД (добавить новые, обновить описания).
  3. Собрать все Role-объекты.
  4. Upsert в БД.
  5. Для каждой роли установить правильный набор пермишенов.

Важно: сервис НЕ удаляет «лишние» пермишены из БД.
Это защита от случайной потери данных при откате деплоя.
Удаление всегда через явную Alembic-миграцию.
"""

from __future__ import annotations

from identity.domain.entities.permission import Permission, Role, create_permission, create_role
from identity.domain.permissions.constants import (
    PERMISSION_DESCRIPTIONS,
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
)
from identity.domain.permissions.enums import PermissionCodename, RoleName


class PermissionSyncService:
    """
    Доменный сервис: формирует набор пермишенов и ролей для синхронизации с БД.

    Не делает запросов в БД сам — возвращает объекты, которые
    application-сервис персистирует через репозитории.

    Такой дизайн позволяет тестировать бизнес-логику без БД.
    """

    def build_permissions(self) -> list[Permission]:
        """
        Создаёт Permission-объекты из enum + описаний.
        Вызывается перед upsert в БД.

        ID генерируется новый, но upsert в БД использует codename
        как уникальный ключ (ON CONFLICT(codename) DO UPDATE).
        """
        return [
            create_permission(
                codename=perm.value,
                description=PERMISSION_DESCRIPTIONS.get(perm, ""),
            )
            for perm in PermissionCodename
        ]

    def build_roles(self) -> list[Role]:
        """
        Создаёт Role-объекты из enum + описаний.
        Без пермишенов — связи устанавливаются отдельно.
        """
        return [
            create_role(
                name=role.value,
                description=ROLE_DESCRIPTIONS.get(role, ""),
            )
            for role in RoleName
        ]

    def get_role_permission_codenames(self, role_name: str) -> list[str]:
        """
        Возвращает список codename пермишенов для роли.

        Args:
            role_name: строковое имя роли (из RoleName.value)
            description: описание роли

        Returns:
            Список codename пермишенов.
            Пустой список если роль не найдена.
        """
        try:
            role = RoleName(value=role_name)
        except ValueError:
            return []
        return [p.value for p in ROLE_PERMISSIONS.get(role.value, [])]

    def validate_codename_exists(self, codename: str) -> bool:
        """Проверяет что codename зарегистрирован в системе."""
        return codename in {p.value for p in PermissionCodename}

    def get_all_codenames(self) -> frozenset[str]:
        """Все зарегистрированные codename."""
        return frozenset(p.value for p in PermissionCodename)

    def get_default_role_name(self) -> str:
        """Роль по умолчанию для новых пользователей."""
        return RoleName.USER.value
