"""
domain/entities/permission.py

Доменные сущности системы разрешений.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.utils import generate_uuid


@dataclass
class PermissionEntity:
    """Разрешение — атомарное право на действие."""

    id: str
    codename: str  # "family:create:any" — уникальный строковый ключ
    description: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PermissionEntity):
            return NotImplemented
        return self.codename == other.codename

    def __hash__(self) -> int:
        return hash(self.codename)


@dataclass
class RoleEntity:
    """Роль — именованная группа разрешений."""

    id: str
    name: str  # "admin", "user", "moderator"
    description: str = ""
    permissions: list[PermissionEntity] = field(default_factory=list)

    def has_permission(self, codename: str) -> bool:
        return any(p.codename == codename for p in self.permissions)

    def get_permission_codenames(self) -> frozenset[str]:
        return frozenset(p.codename for p in self.permissions)


@dataclass
class RolePermissionEntity:
    id: str
    permission_id: str
    role_id: str


@dataclass
class AccountRoleEntity:
    id: str
    account_id: str
    role_id: str


def create_permission_entity(
    codename: str,
    description: str = "",
):
    return PermissionEntity(
        id=generate_uuid(),
        codename=codename,
        description=description,
    )


def create_role_entity(
    name: str,
    description: str = "",
    permissions: list[PermissionEntity] = None,
):
    return RoleEntity(id=generate_uuid(), name=name, description=description, permissions=permissions)


def create_role_permission_entity(
    role_id: str,
    permission_id: str,
):
    return RolePermissionEntity(
        id=generate_uuid(),
        role_id=role_id,
        permission_id=permission_id,
    )


def create_account_role_entity(
    account_id: str,
    role_id: str,
):
    return AccountRoleEntity(
        id=generate_uuid(),
        account_id=account_id,
        role_id=role_id,
    )
