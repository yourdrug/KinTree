"""
domain/entities/account.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from shared.domain.utils import generate_uuid


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_PASSWORD_HASH_LENGTH = 20  # bcrypt hashes are 60 chars; anything shorter is suspicious


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

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Account id cannot be empty.")
        if not self.email or not self.email.strip():
            raise ValueError("Account email cannot be empty.")
        if not _EMAIL_RE.match(self.email):
            raise ValueError(f"Account email {self.email!r} is not a valid email address.")
        if not self.hashed_password:
            raise ValueError("Account hashed_password cannot be empty.")
        if len(self.hashed_password) < _MIN_PASSWORD_HASH_LENGTH:
            raise ValueError("Account hashed_password appears too short to be a valid hash.")
        if not self.role_name or not self.role_name.strip():
            raise ValueError("Account role_name cannot be empty.")

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
    if not email or not email.strip():
        raise ValueError("email cannot be empty.")

    if not hashed_password:
        raise ValueError("hashed_password cannot be empty.")

    return Account(
        id=generate_uuid(),
        email=email.strip().lower(),
        hashed_password=hashed_password,
        role_name="user",
        permissions=frozenset(),
    )
