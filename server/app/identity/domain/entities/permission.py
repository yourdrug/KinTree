"""
identity/domain/entities/permission.py

Role — Entity системы разрешений.

Permission остаётся в value_objects/permission.py.
Фабрики здесь — для удобства импорта в тестах и application-слое.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.utils import generate_uuid

from identity.domain.value_objects.permission import Permission


@dataclass(frozen=True)
class Role:
    """
    Entity: именованная группа разрешений.

    frozen=True:
      - Гарантирует, что permissions не изменится после создания.
      - Делает Role hashable по умолчанию (через __hash__ ниже).
      - Устраняет класс ошибок "изменили permissions, кэш устарел".

    Идентичность — по id (не по набору permissions).
    """

    id: str
    name: str
    description: str = ""
    permissions: frozenset[Permission] = field(default_factory=frozenset)

    @property
    def codenames(self) -> frozenset[str]:
        """O(1) set для проверки has_permission. Вычисляется из permissions."""
        return frozenset(p.codename for p in self.permissions)

    def has_permission(self, codename: str) -> bool:
        """Проверка пермишена по codename."""
        return codename in self.codenames

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


# ── Фабрики ───────────────────────────────────────────────────────────────────


def create_permission(codename: str, description: str = "") -> Permission:
    """Фабрика Permission. Генерирует id."""
    return Permission(id=generate_uuid(), codename=codename, description=description)


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
