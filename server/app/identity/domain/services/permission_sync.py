"""
identity/domain/services/permission_sync.py

Доменный сервис синхронизации пермишенов.
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

    Не делает запросов в БД — возвращает объекты, которые
    application-сервис персистирует через репозитории.
    """

    def build_permissions(self) -> list[Permission]:
        """Создаёт Permission-объекты из enum + описаний."""
        return [
            create_permission(
                codename=perm.value,
                description=PERMISSION_DESCRIPTIONS.get(perm, ""),
            )
            for perm in PermissionCodename
        ]

    def build_roles(self) -> list[Role]:
        """Создаёт Role-объекты из enum + описаний. Без пермишенов — связи устанавливаются отдельно."""
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

        Исправление: конвертируем str → RoleName enum перед lookup,
        т.к. ROLE_PERMISSIONS использует RoleName как ключ.

        Возвращает [] если роль не найдена в словаре.
        """
        try:
            role_enum = RoleName(role_name)
        except ValueError:
            return []
        return [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]

    def validate_codename_exists(self, codename: str) -> bool:
        """Проверяет что codename зарегистрирован в системе."""
        return codename in {p.value for p in PermissionCodename}

    def get_all_codenames(self) -> frozenset[str]:
        """Все зарегистрированные codename."""
        return frozenset(p.value for p in PermissionCodename)

    def get_default_role_name(self) -> str:
        """Роль по умолчанию для новых пользователей."""
        return RoleName.USER.value
