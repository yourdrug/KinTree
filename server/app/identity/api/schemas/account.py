from __future__ import annotations

from pydantic import BaseModel, Field

from identity.application.password.commands import ResetPasswordCommand
from identity.domain.entities.account import Account


class AccountResponse(BaseModel):
    """Схема, которая возвращает данные аккаунта"""

    id: str
    email: str
    is_verified: bool
    is_acc_blocked: bool
    role: str
    permissions: list[str]

    @classmethod
    def from_domain(cls, account: Account) -> AccountResponse:
        return cls(
            id=account.id,
            email=account.email_str,
            is_verified=account.is_verified,
            is_acc_blocked=account.is_acc_blocked,
            role=account.role_name,
            permissions=sorted(account.permissions),
        )


class ResetPasswordRequest(BaseModel):
    """Установка нового пароля по токену из письма."""

    token: str = Field(..., min_length=1, description="Токен из письма сброса пароля")
    new_password: str = Field(..., min_length=8, max_length=128, examples=["NewStr0ngPass!"])

    def to_command(self) -> ResetPasswordCommand:
        return ResetPasswordCommand(token=self.token, new_password=self.new_password)
