"""
identity/domain/entities/permission.py

Доменные сущности системы разрешений.

DDD-принципы:
- Role — Entity (имеет идентификатор, содержит Permission'ы)

"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.utils import generate_uuid

from identity.domain.value_objects.account_role import AccountRole
from identity.domain.value_objects.permission import Permission


# ── Role (Entity) ─────────────────────────────────────────────────────────────


@dataclass
class Role:
    """
    Entity: именованная группа разрешений.

    Идентичность определяется id.
    Содержит набор Permission'ов — неизменяемый frozenset для O(1) проверки.
    """

    id: str
    name: str
    description: str = ""
    permissions: frozenset[Permission] = field(default_factory=frozenset)

    def has_permission(self, codename: str) -> bool:
        """O(1) проверка через frozenset."""
        return any(p.codename == codename for p in self.permissions)

    def get_codenames(self) -> frozenset[str]:
        return frozenset(p.codename for p in self.permissions)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# ── Фабрики ───────────────────────────────────────────────────────────────────


def create_permission(
    codename: str,
    description: str = "",
) -> Permission:
    """Фабрика Permission. Генерирует id."""
    return Permission(
        id=generate_uuid(),
        codename=codename,
        description=description,
    )


def create_role(
    name: str,
    description: str = "",
    permissions: list[Permission] | None = None,
) -> Role:
    """Фабрика Role. Генерирует id."""
    return Role(
        id=generate_uuid(),
        name=name,
        description=description,
        permissions=frozenset(permissions or []),
    )


def create_account_role(
    account_id: str,
    role_id: str,
) -> AccountRole:
    """Фабрика AccountRole. Генерирует id."""
    return AccountRole(
        id=generate_uuid(),
        account_id=account_id,
        role_id=role_id,
    )
