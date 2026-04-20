"""
domain/entities/permission.py

Доменные сущности системы разрешений.

DDD-принципы:
- Permission — Value Object (определяется codename, неизменяем)
- Role       — Entity (имеет идентификатор, содержит Permission'ы)
- AccountRole — Value Object (связь аккаунт-роль, нет собственного поведения)

Важно: бизнес-логика «кто что может» живёт ТОЛЬКО здесь.
Инфраструктура только хранит и читает.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.utils import generate_uuid


# ── Permission (Value Object) ─────────────────────────────────────────────────


@dataclass(frozen=True)
class Permission:
    """
    Value Object: атомарное право на действие.

    Идентичность определяется исключительно codename.
    Два объекта с одинаковым codename — один и тот же пермишен.
    """

    id: str
    codename: str
    description: str = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return NotImplemented
        return self.codename == other.codename

    def __hash__(self) -> int:
        return hash(self.codename)

    def __str__(self) -> str:
        return self.codename


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


# ── AccountRole (Value Object) ────────────────────────────────────────────────


@dataclass(frozen=True)
class AccountRole:
    """
    Value Object: связь аккаунт → роль.

    Не имеет собственного поведения — только данные.
    Один аккаунт имеет ровно одну роль.
    """

    id: str
    account_id: str
    role_id: str


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
