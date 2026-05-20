"""
identity/domain/entities/account.py

Account — корневой агрегат Identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.exceptions import AccountBlockedError, AccountDomainError
from shared.domain.permissions.enums import RoleName
from shared.domain.utils import generate_uuid

from identity.domain.value_objects.email import Email
from identity.domain.value_objects.hashed_password import HashedPassword


@dataclass
class Account:
    id: str
    email: Email
    role_name: RoleName
    hashed_password: HashedPassword | None = None
    is_acc_blocked: bool = False
    is_verified: bool = False
    permissions: frozenset[str] = field(default_factory=frozenset)

    def is_active(self) -> bool:
        return not self.is_acc_blocked

    def has_permission(self, codename: str) -> bool:
        return codename in self.permissions

    def has_any_permission(self, codenames: list[str]) -> bool:
        return any(c in self.permissions for c in codenames)

    def has_all_permissions(self, codenames: list[str]) -> bool:
        return all(c in self.permissions for c in codenames)

    def check_not_blocked(self) -> None:
        """Бросает AccountBlockedError если аккаунт заблокирован."""
        if self.is_acc_blocked:
            raise AccountBlockedError()

    def block(self) -> Account:
        """
        Заблокировать аккаунт.
        Идемпотентно: повторный вызов не бросает исключение.
        """
        self.is_acc_blocked = True
        return self

    def unblock(self) -> Account:
        self.is_acc_blocked = False
        return self

    def verify_email(self) -> Account:
        """
        Подтвердить email.
        Идемпотентно: если уже подтверждён — no-op.
        """
        self.is_verified = True
        return self

    def set_password(self, hashed_password: HashedPassword) -> Account:
        """
        Установить новый хэш пароля.

        Raises:
            AccountDomainError: если передан пустой хэш.
        """
        if hashed_password.value is None:
            raise AccountDomainError(
                errors={"password": "Хэш пароля не может быть пустым"},
            )
        self.hashed_password = hashed_password
        return self

    def has_password(self) -> bool:
        """OAuth-аккаунты создаются без пароля."""
        return self.hashed_password is not None and self.hashed_password.value is not None

    @property
    def email_str(self) -> str:
        return str(self.email)

    @property
    def role_str(self) -> str:
        return self.role_name.value

    @property
    def hashed_password_str(self) -> str | None:
        if not self.has_password():
            return None
        return str(self.hashed_password)


def create_account(
    email: Email,
    hashed_password: HashedPassword | None,
    is_verified: bool = False,
) -> Account:
    """
    Фабрика Account.

    Новый аккаунт создаётся с ролью USER и пустыми permissions.
    Роль назначается отдельно через AccountRoleRepository после сохранения.
    """
    return Account(
        id=generate_uuid(),
        email=email,
        hashed_password=hashed_password,
        is_verified=is_verified,
        role_name=RoleName.USER,
        permissions=frozenset(),
    )
