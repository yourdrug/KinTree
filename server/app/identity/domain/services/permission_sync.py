"""
identity/domain/services/permission_sync.py

Доменный сервис синхронизации пермишенов.
"""

from __future__ import annotations

from identity.domain.entities.permission import Permission, Role, create_permission, create_role
from identity.domain.permissions.constants import ROLE_PERMISSIONS
from identity.domain.permissions.enums import PermissionCodename, RoleName


class PermissionSyncService:
    """Доменный сервис: формирует набор пермишенов и ролей для синхронизации с БД."""

    def build_permissions(self) -> list[Permission]:
        """Создаёт Permission-объекты из enum + описаний."""
        return [
            create_permission(
                codename=perm.value,
                description=perm.description,
            )
            for perm in PermissionCodename
        ]

    def build_roles(self) -> list[Role]:
        """Создаёт Role-объекты из enum + описаний."""
        return [
            create_role(
                name=role.value,
                description=role.description,
            )
            for role in RoleName
        ]

    def get_role_permission_codenames(self, role: Role) -> list[str]:
        """
        Возвращает список codename пермишенов для роли.

        Возвращает [] если роль не найдена в словаре.
        """
        role_name: RoleName = RoleName.get_by_name(name=role.name)
        return [p.value for p in ROLE_PERMISSIONS.get(role_name, [])]
