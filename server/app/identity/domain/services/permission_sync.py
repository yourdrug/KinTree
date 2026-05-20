"""
identity/domain/services/permission_sync.py

PermissionSyncPolicy — чистый доменный объект.
"""

from __future__ import annotations

from shared.domain.permissions.constants import ROLE_PERMISSIONS
from shared.domain.permissions.enums import PermissionCodename, RoleName

from identity.domain.entities.permission import Permission, Role, create_permission, create_role


class PermissionSyncPolicy:
    """Политика синхронизации: что должно быть в БД."""

    def build_permissions(self) -> list[Permission]:
        """Создаёт Permission-объекты из enum + описаний."""
        return [create_permission(codename=perm.value, description=perm.description) for perm in PermissionCodename]

    def build_roles(self) -> list[Role]:
        """Создаёт Role-объекты из enum + описаний."""
        return [create_role(name=role.value, description=role.description) for role in RoleName]

    def get_role_permission_codenames(self, role: Role) -> list[str]:
        role_name = RoleName.get_by_name(name=role.name)
        return [p.value for p in ROLE_PERMISSIONS.get(role_name, [])]
