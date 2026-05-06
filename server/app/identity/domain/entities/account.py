"""
identity/domain/entities/account.py

Account — корневой агрегат Identity bounded context.

Изменения относительно предыдущей версии:
- email хранится как Email VO (нормализация и валидация в домене)
- hashed_password хранится как HashedPassword VO (инварианты хэша в домене)
- role_name типизирован как RoleName (не сырая строка)
- Убрана _validate() — инварианты теперь в VO через __post_init__
- create_account принимает уже готовые VO — фабрика не дублирует валидацию
- permissions остаётся frozenset[str] — O(1) поиск важнее типизации здесь
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.utils import generate_uuid

from identity.domain.entities.permission import get_default_role_name
from identity.domain.permissions.enums import RoleName
from identity.domain.value_objects.email import Email
from identity.domain.value_objects.hashed_password import HashedPassword


@dataclass
class Account:
    id: str
    email: Email
    hashed_password: HashedPassword
    role_name: RoleName
    is_acc_blocked: bool = False
    is_verified: bool = False
    # frozenset[str] — codenames для O(1) has_permission. Загружаются JOIN-ом.
    permissions: frozenset[str] = field(default_factory=frozenset)

    # ── Queries ───────────────────────────────────────────────────────────────

    def is_active(self) -> bool:
        return not self.is_acc_blocked

    def has_permission(self, codename: str) -> bool:
        return codename in self.permissions

    def has_any_permission(self, codenames: list[str]) -> bool:
        return any(c in self.permissions for c in codenames)

    def has_all_permissions(self, codenames: list[str]) -> bool:
        return all(c in self.permissions for c in codenames)

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def email_str(self) -> str:
        """Нормализованный email как строка — для JWT payload, логов и т.д."""
        return str(self.email)

    @property
    def role_str(self) -> str:
        """Строковое имя роли — для JWT payload и API-ответов."""
        return self.role_name.value


def create_account(email: Email, hashed_password: HashedPassword) -> Account:
    """
    Фабрика Account.

    Принимает уже валидированные VO — не дублирует валидацию.
    Новый аккаунт всегда создаётся с ролью USER и пустыми permissions
    (роль назначается отдельно после регистрации через AccountRoleRepository).
    """
    return Account(
        id=generate_uuid(),
        email=email,
        hashed_password=hashed_password,
        role_name=get_default_role_name(),
        permissions=frozenset(),
    )
