"""
domain/entities/account.py
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.utils import generate_uuid


@dataclass
class Account:
    id: str
    email: str
    hashed_password: str
    is_acc_blocked: bool = False
    is_verified: bool = False
    refresh_token: str | None = None

    # Роль хранится как строка (name из таблицы roles)
    role_name: str = "user"

    # Разрешения загружаются вместе с аккаунтом через JOIN
    # Хранятся как frozenset для быстрой O(1) проверки
    permissions: frozenset[str] = field(default_factory=frozenset)

    def is_active(self) -> bool:
        return not self.is_acc_blocked

    def has_permission(self, codename: str) -> bool:
        """O(1) проверка разрешения."""
        return codename in self.permissions

    def has_any_permission(self, codenames: list[str]) -> bool:
        return any(c in self.permissions for c in codenames)

    def has_all_permissions(self, codenames: list[str]) -> bool:
        return all(c in self.permissions for c in codenames)


def create_account(email: str, hashed_password: str) -> Account:
    return Account(
        id=generate_uuid(),
        email=email,
        hashed_password=hashed_password,
        role_name="user",
        permissions=frozenset(),
    )
