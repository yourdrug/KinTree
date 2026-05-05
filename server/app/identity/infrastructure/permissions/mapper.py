"""
identity/infrastructure/permissions/mapper.py

Маппер: ORM-модели ↔ доменные объекты системы разрешений.

"""

from __future__ import annotations

from identity.domain.entities.account_role import AccountRole
from identity.domain.entities.permission import Role
from identity.domain.value_objects.permission import Permission
from identity.infrastructure.db.models.permission import AccountRole as AccountRoleORM
from identity.infrastructure.db.models.permission import Permission as PermissionORM
from identity.infrastructure.db.models.permission import Role as RoleORM


class PermissionMapper:
    @staticmethod
    def to_domain(orm: PermissionORM) -> Permission:
        return Permission(
            id=orm.id,
            codename=orm.codename,
            description=orm.description,
        )

    @staticmethod
    def to_persistence(entity: Permission) -> dict:
        return {
            "id": entity.id,
            "codename": entity.codename,
            "description": entity.description,
        }


class RoleMapper:
    @staticmethod
    def to_domain(
        orm: RoleORM,
        permissions: list[Permission] | None = None,
    ) -> Role:
        return Role(
            id=orm.id,
            name=orm.name,
            description=orm.description,
            permissions=frozenset(permissions or []),
        )

    @staticmethod
    def to_persistence(entity: Role) -> dict:
        return {
            "id": entity.id,
            "name": entity.name,
            "description": entity.description,
        }


class AccountRoleMapper:
    @staticmethod
    def to_domain(orm: AccountRoleORM) -> AccountRole:
        return AccountRole(
            id=orm.id,
            account_id=orm.account_id,
            role_id=orm.role_id,
        )

    @staticmethod
    def to_persistence(entity: AccountRole) -> dict:
        return {
            "id": entity.id,
            "account_id": entity.account_id,
            "role_id": entity.role_id,
        }
