"""
domain/entities/permission.py

Доменные сущности системы разрешений.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PermissionEntity:
    """Разрешение — атомарное право на действие."""

    id: str
    codename: str          # "family:create" — уникальный строковый ключ
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
    name: str              # "admin", "user", "moderator"
    description: str = ""
    permissions: list[PermissionEntity] = field(default_factory=list)

    def has_permission(self, codename: str) -> bool:
        return any(p.codename == codename for p in self.permissions)

    def get_permission_codenames(self) -> frozenset[str]:
        return frozenset(p.codename for p in self.permissions)
