"""
identity/api/schemas/auth.py

API-схемы для auth эндпоинтов.
"""

from __future__ import annotations

from presentation.rest.dependencies.request_meta import RequestMeta
from pydantic import BaseModel, EmailStr, Field

from identity.application.auth.commands import LoginCommand, RegisterCommand


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass1!"])

    def to_command(self) -> RegisterCommand:
        return RegisterCommand(email=self.email, password=self.password)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=1, examples=["StrongPass1!"])

    def to_command(self, meta: RequestMeta) -> LoginCommand:
        return LoginCommand(
            email=self.email,
            password=self.password,
            user_agent=meta.user_agent,
            ip_address=meta.ip_address,
        )


class TokenResponse(BaseModel):
    """
    Ответ при логине/рефреше.

    permissions — список всех codename разрешений пользователя.
    Клиент может закэшировать и использовать для UI-логики
    (показать/скрыть кнопки) без дополнительных запросов.

    Пример:
        {
          "access_token": "eyJ...",
          "refresh_token": "eyJ...",
          "token_type": "bearer",
          "role": "user",
          "permissions": ["family:create", "family:read", "person:create", ...]
        }
    """

    access_token: str
    refresh_token: str
    role: str
    permissions: list[str] = Field(description="Отсортированный список codename всех разрешений")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class AccountResponse(BaseModel):
    id: str
    email: str
    is_verified: bool
    is_acc_blocked: bool
    role: str
    permissions: list[str]

    model_config = {"from_attributes": True}
