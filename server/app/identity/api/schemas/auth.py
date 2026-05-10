"""
identity/api/schemas/auth.py

API-схемы для auth эндпоинтов.
"""

from __future__ import annotations

from presentation.rest.dependencies.request_meta import RequestMeta
from pydantic import BaseModel, EmailStr, Field

from identity.application.auth.commands import LoginCommand, RegisterCommand, TokenPair


class RegisterRequest(BaseModel):
    """
    Схема для регистрации пользователя

    Нет никаких валидаций, все валидируется в домене
    """

    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongPass1!"])

    def to_command(self) -> RegisterCommand:
        return RegisterCommand(email=self.email, password=self.password)


class LoginRequest(BaseModel):
    """Схема для входа пользователя"""

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
    """

    access_token: str
    refresh_token: str
    role: str
    permissions: list[str]

    @classmethod
    def from_command(cls, token_pair: TokenPair) -> TokenResponse:
        return cls(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            role=token_pair.role,
            permissions=token_pair.permissions,
        )


class RefreshRequest(BaseModel):
    """Схема для обновления refresh токена на bearer endpoint"""

    refresh_token: str = Field(..., min_length=1)
