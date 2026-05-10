"""
identity/api/schemas/email.py

Pydantic-схемы для email эндпоинтов.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from identity.application.email.commands import (
    ForgotPasswordCommand,
    VerifyEmailCommand,
)


class VerifyEmailRequest(BaseModel):
    """Подтверждение email по токену из письма."""

    token: str = Field(..., min_length=1, description="Токен из письма подтверждения")

    def to_command(self) -> VerifyEmailCommand:
        return VerifyEmailCommand(token=self.token)


class ForgotPasswordRequest(BaseModel):
    """Запрос на сброс пароля — только email."""

    email: EmailStr = Field(..., examples=["user@example.com"])

    def to_command(self) -> ForgotPasswordCommand:
        return ForgotPasswordCommand(email=self.email)
